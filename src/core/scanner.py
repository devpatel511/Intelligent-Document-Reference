import os
import hashlib
import time
from typing import Generator, Tuple, Dict, Any
import logging

class FileScanner:
    def __init__(self, root_paths: list[str], ignore_patterns: list[str] = None):
        self.root_paths = root_paths
        self.ignore_patterns = ignore_patterns or []
        self.logger = logging.getLogger(__name__)

    def calculate_hash(self, file_path: str, block_size=65536) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    sha256.update(block)
            return sha256.hexdigest()
        except OSError:
            return None

    def scan_directory(self, path: str) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        for root, dirs, files in os.walk(path):
            # Filter directories
            # TODO: Implement proper ignore pattern logic (like .gitignore)
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stats = os.stat(file_path)
                    file_info = {
                        "path": file_path,
                        "mtime": stats.st_mtime,
                        "size": stats.st_size,
                        # Hash is expensive, might want to defer or do only if mtime/size changed
                        # For now, we return basic stats, hash calculation can happen on demand
                    }
                    yield file_path, file_info
                except OSError as e:
                    self.logger.error(f"Error accessing {file_path}: {e}")

    def scan_all(self):
        self.logger.info("Starting full scan")
        results = []
        for root in self.root_paths:
            if os.path.exists(root):
                for path, info in self.scan_directory(root):
                    results.append(info)
        return results
