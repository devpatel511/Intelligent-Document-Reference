"""Persistent cache for vision LLM image descriptions. Survives app restarts."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Default: project root (parent of ingestion package)
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "image_description_cache.db"


class ImageDescriptionCache:
    """SQLite-backed cache: (path, mtime) -> description. Invalidates when file changes."""

    def __init__(self, db_path: Optional[os.PathLike[str]] = None):
        self._path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_descriptions (
                    path TEXT PRIMARY KEY,
                    mtime REAL NOT NULL,
                    description TEXT NOT NULL
                )
                """)
            conn.commit()

    def get(self, path: str, mtime: float) -> Optional[str]:
        """Return cached description if path and mtime match; else None."""
        path = os.path.abspath(os.path.normpath(path))
        with sqlite3.connect(self._path) as conn:
            row = conn.execute(
                "SELECT description FROM image_descriptions WHERE path = ? AND mtime = ?",
                (path, mtime),
            ).fetchone()
        return row[0] if row else None

    def set(self, path: str, mtime: float, description: str) -> None:
        """Store description for (path, mtime). Overwrites if path already exists."""
        path = os.path.abspath(os.path.normpath(path))
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO image_descriptions (path, mtime, description)
                VALUES (?, ?, ?)
                """,
                (path, mtime, description),
            )
            conn.commit()


# Singleton for use in parser (avoids passing cache through every layer)
_cache: Optional[ImageDescriptionCache] = None


def get_image_description_cache(
    db_path: Optional[os.PathLike[str]] = None,
) -> ImageDescriptionCache:
    """Return the global image description cache, creating it if needed."""
    global _cache
    if _cache is None:
        _cache = ImageDescriptionCache(db_path=db_path)
    return _cache
