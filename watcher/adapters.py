import platform
import logging
from abc import ABC, abstractmethod
from typing import Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BaseWatcher(ABC):
    def __init__(self, callback: Callable):
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def start(self, paths: List[str]):
        pass

    @abstractmethod
    def stop(self):
        pass

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, callback, excluded_files=None):
        self.callback = callback
        self.excluded_files = set(excluded_files) if excluded_files else set()

    def _is_excluded(self, path):
        import os
        return os.path.abspath(path) in self.excluded_files

    def on_modified(self, event):
        if not event.is_directory and not self._is_excluded(event.src_path):
            self.callback(event.src_path, "modified")

    def on_created(self, event):
        if not event.is_directory and not self._is_excluded(event.src_path):
            self.callback(event.src_path, "created")

    def on_deleted(self, event):
        if not event.is_directory and not self._is_excluded(event.src_path):
            self.callback(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory and not self._is_excluded(event.src_path):
            self.callback(event.src_path, "moved", dest_path=event.dest_path)

class CrossPlatformWatcher(BaseWatcher):
    def __init__(self, callback: Callable):
        super().__init__(callback)
        self.observer = Observer()
        self.os_type = platform.system()
        self.logger.info(f"Initialized Watcher for OS: {self.os_type}")
        self._watched_paths = {}

    def start(self, paths: List[str]):
        # Initial bulk start
        for path in paths:
             # Default behavior for start() list
            self.schedule_watch(path, [])
        self.observer.start()

    def schedule_watch(self, path: str, excluded_files: List[str]):
        if path in self._watched_paths:
            return # Already watched
            
        import os
        if not os.path.exists(path):
            self.logger.warning(f"Path does not exist: {path}")
            return

        handler = WatchdogHandler(self.callback, excluded_files=excluded_files)
        # recursive=True is default requirement
        self.logger.info(f"Scheduling watcher for: {path}")
        watch = self.observer.schedule(handler, path, recursive=True)
        self._watched_paths[path] = watch

    def unschedule_watch(self, path: str):
        if path in self._watched_paths:
            self.observer.unschedule(self._watched_paths[path])
            del self._watched_paths[path]
            self.logger.info(f"Stopped watching: {path}")

    def get_watched_paths(self) -> List[str]:
        return list(self._watched_paths.keys())

    def stop(self):


        self.observer.stop()
        self.observer.join()

def get_watcher(callback: Callable) -> BaseWatcher:
    # In a pure "plug-in" manual implementation, we would selectively
    # instantiate LinuxInotifyWatcher, WindowsReadDirWatcher etc.
    # checking platform.system(). 
    # Since watchdog handles this internally, we wrap it.
    return CrossPlatformWatcher(callback)
