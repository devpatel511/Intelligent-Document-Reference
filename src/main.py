import time
import logging
import sys
import os
import threading
from core.database import FileRegistry
from core.scanner import FileScanner
from watcher.adapters import get_watcher

# Determine the directory where the application is running
if getattr(sys, 'frozen', False):
    # If running as a compiled .exe (PyInstaller)
    APP_DIR = os.path.dirname(sys.executable)
else:
    # If running as a python script
    # We want the root project folder, not src/
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define paths for data
DB_PATH = os.path.join(APP_DIR, "file_registry.db")
LOG_PATH = os.path.join(APP_DIR, "service.log")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH)
    ]
)
logger = logging.getLogger("IntelligentDocRef")

class FileTrackingService:
    def __init__(self, watch_paths: list[str]):
        self.watch_paths = watch_paths
        self.db = FileRegistry(db_path=DB_PATH)
        self.scanner = FileScanner(watch_paths)
        self.watcher = get_watcher(self.handle_event)
    
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
            
        else: # created or modified
            self._update_inventory(src_path)
            self.db.add_event(src_path, event_type)

    def _update_inventory(self, file_path: str):
        """Updates the watched_files table with current metadata (last_modified only)."""
        try:
            if os.path.exists(file_path):
                stats = os.stat(file_path)
                self.db.upsert_file(file_path, stats.st_mtime)
        except OSError:
            pass # File might be gone

    def start(self):
        logger.info("Service Starting...")
        
        # 1. Initial Scan (Populate Inventory & Enqueue)
        logger.info("Performing Initial Scan...")
        files = self.scanner.scan_all()
        for f in files:
            # Add to Inventory (watched_files)
            self.db.upsert_file(f['path'], f['mtime'])
            # Add Modification Event
            self.db.add_event(f['path'], 'modified')
        
        # 2. Start Queue Worker
        # User requested to leave items as 'incomplete' for external processing.
        # We invoke the worker manually or leave it for an external agent.
        # worker_thread = threading.Thread(target=self.process_queue_worker, daemon=True)
        # worker_thread.start()

        # 3. Start Watcher
        logger.info("Starting OS File Watcher...")
        self.watcher.start(self.watch_paths)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Stopping Service...")
        self.watcher.stop()

if __name__ == "__main__":
    # In a real app, these paths would come from a config file
    paths_to_watch = [os.path.abspath("./test_watch_folder")]
    
    # Ensure test folder exists
    if not os.path.exists(paths_to_watch[0]):
        os.makedirs(paths_to_watch[0])
        
    service = FileTrackingService(paths_to_watch)
    service.start()
