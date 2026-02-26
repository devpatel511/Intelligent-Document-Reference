"""File crawler: recursive scan for supported RAG document types."""

import hashlib
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from rag.config import RAGPipelineConfig


@dataclass
class DiscoveredFile:
    """A file discovered by the crawler."""

    path: Path
    file_name: str
    extension: str
    size_bytes: int
    modified_timestamp: float
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash and self.path.exists():
            self.content_hash = _file_hash(self.path)


def _file_hash(path: Path) -> str:
    """SHA256 hash of file content for change detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _matches_exclude(path: Path, patterns: tuple[str, ...], root: Path) -> bool:
    """True if path matches any exclude pattern."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    rel_str = str(rel).replace("\\", "/")
    for pat in patterns:
        if fnmatch.fnmatch(rel_str, pat) or fnmatch.fnmatch(str(path), pat):
            return True
    return False


def crawl_directory(
    root: Path,
    config: RAGPipelineConfig,
) -> Iterator[DiscoveredFile]:
    """Recursively discover supported files in directory.

    Yields DiscoveredFile for each file matching supported_extensions,
    respecting exclude_patterns and max_file_size_mb.
    """
    root = Path(root).resolve()
    ext_set = frozenset(config.supported_extensions)
    max_bytes = int(config.max_file_size_mb * 1024 * 1024)

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ext_set:
            continue
        if _matches_exclude(path, config.exclude_patterns, root):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_size > max_bytes:
            continue
        yield DiscoveredFile(
            path=path,
            file_name=path.name,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_timestamp=stat.st_mtime,
        )
