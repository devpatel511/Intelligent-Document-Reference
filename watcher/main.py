import logging
import os
import sys
import threading
import time

from adapters import get_watcher

from core.database import FileRegistry
from core.scanner import FileScanner

# Determine the directory where the application is running
if getattr(sys, "frozen", False):
    # If running as a compiled .exe (PyInstaller)
    APP_DIR = os.path.dirname(sys.executable)
else:
    # If running as a python script
    # We want the root project folder, not src/
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define paths for data
DB_PATH = os.path.join(APP_DIR, "file_registry.db")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("IntelligentDocRef")


class FileTrackingService:
    def __init__(self):
        self.db = FileRegistry(db_path=DB_PATH)
        self.watch_configs = {}  # path -> config dict
        self.scanner = FileScanner([])  # Roots will be handled dynamically
        self.watcher = get_watcher(self.handle_event)
        self.running = False
        self.sync_thread = None

    def refresh_configs(self):
        """Load configs from DB."""
        try:
            configs = self.db.get_watch_paths()
            return {c["path"]: c for c in configs}
        except Exception as e:
            logger.error(f"Failed to refresh configs: {e}")
            return {}

    def handle_event(self, src_path: str, event_type: str, dest_path: str = None):
        logger.info(f"Event Detected: {event_type} - {src_path}")

        if event_type == "deleted":
            self.db.remove_file(src_path)
            self.db.add_event(src_path, "deleted")

        elif event_type == "moved" and dest_path:
            # Handle move as delete old + create new
            self.db.remove_file(src_path)
            self.db.add_event(src_path, "deleted")

            self._update_inventory(dest_path)
            self.db.add_event(dest_path, "created")

        else:  # created or modified
            self._update_inventory(src_path)
            self.db.add_event(src_path, event_type)

    def _update_inventory(self, file_path: str):
        """Updates the watched_files table with current metadata (last_modified only)."""
        try:
            if os.path.exists(file_path):
                stats = os.stat(file_path)
                self.db.upsert_file(file_path, stats.st_mtime)
        except OSError:
            pass  # File might be gone

    def _scan_and_index(self, path: str, excluded_files: list[str] = None):
        """Scans a directory and adds files to DB."""
        logger.info(f"Scanning directory: {path}")
        for _, info in self.scanner.scan_directory(path, excluded_files=excluded_files):
            self.db.upsert_file(info["path"], info["mtime"])
            self.db.add_event(info["path"], "modified")

    def _sync_loop(self):
        """Polls DB for changes in watched paths."""
        logger.info("Started config sync loop.")
        while self.running:
            try:
                # 1. Fetch Desired State from DB
                new_configs = self.refresh_configs()
                desired_paths = set(new_configs.keys())

                # 2. Fetch Actual State from Watcher (if supported)
                if hasattr(self.watcher, "get_watched_paths"):
                    actual_paths = set(self.watcher.get_watched_paths())
                else:
                    actual_paths = set(self.watch_configs.keys())  # Fallback

                # 3. Calculate Reconciliation
                # Paths that should be watched but aren't (Added OR Failed previously)
                missing = desired_paths - actual_paths

                # Paths that are watched but shouldn't be (Removed)
                extra = actual_paths - desired_paths

                # Paths that are watched but config changed (Modified)
                # Note: We only check intersection of desired and actual
                modified = []
                common = desired_paths.intersection(actual_paths)
                for path in common:
                    # Check if exclusions changed
                    # Be careful if self.watch_configs doesn't have it (e.g. restart)
                    old_cfg = self.watch_configs.get(path, {})
                    new_cfg = new_configs[path]

                    old_excl = set(old_cfg.get("excluded_files", []))
                    new_excl = set(new_cfg.get("excluded_files", []))
                    if old_excl != new_excl:
                        modified.append(path)

                # 4. Apply Changes
                for path in missing:
                    logger.info(f"Adding/Retrying watch path: {path}")
                    cfg = new_configs[path]
                    excluded = cfg.get("excluded_files", [])
                    self.watcher.schedule_watch(path, excluded)
                    # Only scan if schedule succeeded (check actual paths again or rely on watcher log)
                    # To be safe, we wrap scan in try/catch or check existence
                    if (
                        hasattr(self.watcher, "get_watched_paths")
                        and path in self.watcher.get_watched_paths()
                    ):
                        self._scan_and_index(path, excluded)
                    elif not hasattr(self.watcher, "get_watched_paths"):
                        # Fallback scan
                        self._scan_and_index(path, excluded)

                for path in extra:
                    logger.info(f"Removing watch path: {path}")
                    self.watcher.unschedule_watch(path)

                for path in modified:
                    logger.info(f"Modified config for path: {path}")
                    self.watcher.unschedule_watch(path)

                    cfg = new_configs[path]
                    excluded = cfg.get("excluded_files", [])

                    self.watcher.schedule_watch(path, excluded)
                    self._scan_and_index(path, excluded)

                # Update local cache
                self.watch_configs = new_configs

            except Exception as e:
                logger.error(f"Sync loop error: {e}")

            time.sleep(5)  # Poll every 5 seconds

    def start(self):
        logger.info(f"Service Starting... DB: {DB_PATH}")
        self.running = True

        # 1. Load initial config

        self.watch_configs = self.refresh_configs()

        # 2. Start Watcher (Empty first)
        logger.info("Starting OS File Watcher...")
        self.watcher.start([])

        # 3. Schedule initial paths
        for path, cfg in self.watch_configs.items():
            excluded = cfg.get("excluded_files", [])
            self.watcher.schedule_watch(path, excluded)
            # Initial scan
            self._scan_and_index(path, excluded)

        # 4. Start Sync Thread
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)

        self.sync_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Stopping Service...")
        self.running = False
        self.watcher.stop()


if __name__ == "__main__":
    # Service now relies on DB configuration.
    # Use API or DB tools to add paths.

    # Verify DB Access
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database file not found at {DB_PATH}. It will be created.")

    service = FileTrackingService()
    service.start()
