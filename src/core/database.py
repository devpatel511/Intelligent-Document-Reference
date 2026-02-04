import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class FileRegistry:
    def __init__(self, db_path: str = "file_registry.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watched_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    last_modified REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL
                )
            """)
            conn.commit()

    def add_event(self, path: str, event_type: str):
        """Add a file event to the processing queue. If event exists, update it."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for existing event for this file
            cursor.execute("""
                SELECT id FROM processing_queue 
                WHERE file_path = ?
            """, (path,))
            existing = cursor.fetchone()

            if existing:
                # Update timestamp
                cursor.execute("""
                    UPDATE processing_queue 
                    SET timestamp = ?, event_type = ?
                    WHERE id = ?
                """, (datetime.now().timestamp(), event_type, existing[0]))
            else:
                # Insert new event
                cursor.execute("""
                    INSERT INTO processing_queue (file_path, event_type, timestamp)
                    VALUES (?, ?, ?)
                """, (path, event_type, datetime.now().timestamp()))
            
            conn.commit()

    def pop_next_event(self) -> Optional[Dict[str, Any]]:
        """Fetch and REMOVE the next event (FIFO)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Select oldest event
            cursor.execute("""
                SELECT * FROM processing_queue 
                ORDER BY timestamp ASC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                # DELETE execution happens here - strictly simulating 'popping' from queue
                cursor.execute("DELETE FROM processing_queue WHERE id = ?", (row['id'],))
                conn.commit()
                return dict(row)
            return None

    def upsert_file(self, path: str, last_modified: float):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO watched_files (path, last_modified)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    last_modified=excluded.last_modified
            """, (path, last_modified))
            conn.commit()

    def get_file_state(self, path: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watched_files WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "path": row[1],
                    "last_modified": row[2]
                }
            return None

    def remove_file(self, path: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watched_files WHERE path = ?", (path,))
            conn.commit()
