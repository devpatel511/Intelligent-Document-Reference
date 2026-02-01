import sqlite3
import os
from typing import Optional, List, Dict
from pathlib import Path

class MetadataManager:
    """
    Handles all interactions with the relational metadata database (SQLite).
    This is separate from the Vector DB interactions.
    """
    def __init__(self, db_path: str = "local_search.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Execute the schema.sql to initialize tables."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
            
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        conn = self._get_conn()
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    def register_file(self, path: str, file_hash: str, size: int, modified: float) -> int:
        """
        Upsert a file record. Returns the file_id.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # Check if exists
            cursor.execute("SELECT id, file_hash FROM files WHERE path = ?", (path,))
            row = cursor.fetchone()
            
            if row:
                file_id = row['id']
                # If hash changed, update status
                if row['file_hash'] != file_hash:
                    cursor.execute("""
                        UPDATE files 
                        SET file_hash=?, size_bytes=?, last_modified_timestamp=?, status='outdated'
                        WHERE id=?
                    """, (file_hash, size, modified, file_id))
            else:
                cursor.execute("""
                    INSERT INTO files (path, file_hash, size_bytes, last_modified_timestamp, status)
                    VALUES (?, ?, ?, ?, 'pending')
                    RETURNING id
                """, (path, file_hash, size, modified))
                file_id = cursor.fetchone()[0]
            
            conn.commit()
            return file_id
        finally:
            conn.close()

    def create_version(self, file_id: int, file_hash: str) -> int:
        """Create a version record for a file ingestion run."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO file_versions (file_id, version_hash)
                VALUES (?, ?)
                RETURNING id
            """, (file_id, file_hash))
            version_id = cursor.fetchone()[0]
            conn.commit()
            return version_id
        finally:
            conn.close()

    def add_chunks(self, chunks_data: List[Dict]):
        """
        Batch insert chunk metadata.
        chunks_data must contain: id, file_id, version_id, chunk_index, start_offset, end_offset, text_content
        """
        conn = self._get_conn()
        try:
            conn.executemany("""
                INSERT INTO chunks (id, file_id, version_id, chunk_index, start_offset, end_offset, text_content)
                VALUES (:id, :file_id, :version_id, :chunk_index, :start_offset, :end_offset, :text_content)
            """, chunks_data)
            conn.commit()
        finally:
            conn.close()
    
    def get_file_content(self, file_id: int) -> Optional[str]:
        # Minimal help utility
        conn = self._get_conn()
        cursor = conn.execute("SELECT path FROM files WHERE id = ?", (file_id,))
        res = cursor.fetchone()
        conn.close()
        if res and os.path.exists(res['path']):
            with open(res['path'], 'r', errors='ignore') as f:
                return f.read()
        return None
