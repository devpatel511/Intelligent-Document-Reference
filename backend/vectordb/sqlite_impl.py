import sqlite3
import sqlite_vec
import struct
import json
from typing import List, Dict, Any
from .interface import VectorDBProtocol

class SQLiteVectorDB(VectorDBProtocol):
    def __init__(self, db_path: str = "local_search.db", dim: int = 384):
        self.db_path = db_path
        self.dim = dim
        self.conn = None

    def initialize(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        
        # Create Virtual Vector Table
        # We only store embeddings here.
        self.conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_items USING vec0(
                embedding float[{self.dim}]
            )
        """)
        
        # Mapping table to link integer ROWID (required by vec0) to string UUIDs (used by app)
        # We can also store the metadata here as a JSON string since sqlite-vec is purely for vectors.
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vec_id_map (
                rowid INTEGER PRIMARY KEY,
                external_id TEXT UNIQUE,
                metadata_json TEXT
            )
        """)
        self.conn.commit()

    def add_chunks(self, 
                   embeddings: List[List[float]], 
                   metadata: List[Dict[str, Any]], 
                   ids: List[str]) -> bool:
        if not self.conn:
            self.initialize()
            
        cursor = self.conn.cursor()
        try:
            for i, vector in enumerate(embeddings):
                ext_id = ids[i]
                meta_json = json.dumps(metadata[i]) if metadata and i < len(metadata) else "{}"
                
                # 1. Insert into mapping table to get a ROWID
                # We store metadata here so we can retrieve it during search
                cursor.execute("INSERT OR REPLACE INTO vec_id_map (external_id, metadata_json) VALUES (?, ?)", (ext_id, meta_json))
                row_id = cursor.lastrowid
                
                # 2. Insert into vector table using that ROWID
                # Use the library's serialize_float32 instead of struct.pack
                vec_blob = sqlite_vec.serialize_float32(vector)
                
                cursor.execute("INSERT INTO vec_items(rowid, embedding) VALUES (?, ?)", (row_id, vec_blob))
                
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SQLite Vec Error: {e}")
            self.conn.rollback()
            return False

    def search(self, 
               query_vector: List[float], 
               limit: int = 5) -> List[Dict[str, Any]]:
        if not self.conn:
            self.initialize()
            
        # SQLite-vec search
        cursor = self.conn.cursor()
        
        # We query the vector table first to satisfy the virtual table constraints strictly
        query_blob = sqlite_vec.serialize_float32(query_vector)

        # 1. Get top K rowids from vector table
        # note: vec0 requires 'k = ?' in the WHERE clause or LIMIT
        vec_rows = cursor.execute("""
            SELECT rowid, vec_distance_cosine(embedding, ?) as distance
            FROM vec_items
            WHERE embedding MATCH ?
            AND k = ?
            ORDER BY distance
        """, (query_blob, query_blob, limit)).fetchall()
        
        if not vec_rows:
            return []

        # 2. Fetch the external IDs for those rowids
        results = []
        for rowid, dist in vec_rows:
            res = cursor.execute("SELECT external_id, metadata_json FROM vec_id_map WHERE rowid = ?", (rowid,)).fetchone()
            if res:
                ext_id = res[0]
                meta_json = res[1]
                meta_dict = json.loads(meta_json) if meta_json else {}
                
                results.append({
                    "id": ext_id,
                    "score": 1.0 - dist,
                    "metadata": meta_dict 
                })
            
        return results

    def delete(self, ids: List[str]) -> bool:
        if not self.conn:
            self.initialize()
        # Complex in SQLite: find rowid from map, delete from vec0, delete from map
        cursor = self.conn.cursor()
        try:
            for eid in ids:
                cursor.execute("SELECT rowid FROM vec_id_map WHERE external_id = ?", (eid,))
                row = cursor.fetchone()
                if row:
                    rid = row[0]
                    cursor.execute("DELETE FROM vec_items WHERE rowid = ?", (rid,))
                    cursor.execute("DELETE FROM vec_id_map WHERE rowid = ?", (rid,))
            self.conn.commit()
            return True
        except Exception:
            return False

    def close(self):
        if self.conn:
            self.conn.close()
