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
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path, "modified")

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path, "created")

    def on_deleted(self, event):
        if not event.is_directory:
            self.callback(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory:
            self.callback(event.src_path, "moved", dest_path=event.dest_path)

class CrossPlatformWatcher(BaseWatcher):
    def __init__(self, callback: Callable):
        super().__init__(callback)
        self.observer = Observer()
        self.os_type = platform.system()
        self.logger.info(f"Initialized Watcher for OS: {self.os_type}")

    def start(self, paths: List[str]):
        handler = WatchdogHandler(self.callback)
        for path in paths:
            self.logger.info(f"Scheduling watcher for: {path}")
            self.observer.schedule(handler, path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

def get_watcher(callback: Callable) -> BaseWatcher:
    # In a pure "plug-in" manual implementation, we would selectively
    # instantiate LinuxInotifyWatcher, WindowsReadDirWatcher etc.
    # checking platform.system(). 
    # Since watchdog handles this internally, we wrap it.
    return CrossPlatformWatcher(callback)
