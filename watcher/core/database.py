"""Tracks watched files and monitor configuration via SQLite."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class FileRegistry:
    """Tracks watched files and monitor configuration.

    Uses two tables:
      - ``watched_files`` — per-file metadata (path, last_modified).
      - ``monitor_config`` — active watch-path configuration.
    """

    def __init__(self, db_path: str = "file_registry.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watched_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    last_modified REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitor_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    recursive BOOLEAN DEFAULT 1,
                    excluded_files TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def upsert_file(self, path: str, last_modified: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO watched_files (path, last_modified)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    last_modified=excluded.last_modified
                """,
                (path, last_modified),
            )
            conn.commit()

    def add_watch_path(
        self, path: str, excluded_files: Optional[List[str]] = None
    ) -> None:
        if excluded_files is None:
            excluded_files = []

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO monitor_config (path, excluded_files, is_active)
                VALUES (?, ?, 1)
                ON CONFLICT(path) DO UPDATE SET
                    excluded_files=excluded.excluded_files,
                    is_active=1
                """,
                (path, json.dumps(excluded_files)),
            )
            conn.commit()

    def get_watch_paths(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM monitor_config WHERE is_active = 1"
            ).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["excluded_files"] = (
                    json.loads(d["excluded_files"]) if d["excluded_files"] else []
                )
                results.append(d)
            return results

    def remove_watch_path(self, path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE monitor_config SET is_active = 0 WHERE path = ?", (path,)
            )
            conn.commit()

    def remove_watch_path_by_id(self, config_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE monitor_config SET is_active = 0 WHERE id = ?", (config_id,)
            )
            conn.commit()

    def get_file_state(self, path: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM watched_files WHERE path = ?", (path,)
            ).fetchone()
            if row:
                return {"id": row[0], "path": row[1], "last_modified": row[2]}
            return None

    def remove_file(self, path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM watched_files WHERE path = ?", (path,))
            conn.commit()
