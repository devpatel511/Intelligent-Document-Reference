"""Normalized file event types."""
class FileEvent:
    def __init__(self, path: str, type: str):
        self.path = path
        self.type = type

