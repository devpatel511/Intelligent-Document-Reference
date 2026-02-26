import hashlib
import os
from enum import Enum
from pathlib import Path
from typing import Optional

class ReindexStrategy(Enum):
    SKIP = "skip"                # No action needed
    FULL_INDEX = "full_index"    # Extract, chunk, and embed
    METADATA_UPDATE = "metadata_update" # Update path/mtime only
    PURGE = "purge"              # Remove from DB and Vector store

def calculate_file_hash(path: str) -> str:
    """Calculates SHA-256 hash of file content to detect actual changes."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in 4KB chunks for memory efficiency
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def determine_strategy(
    file_path: str, 
    db_record: Optional[dict], 
    event_type: str = "modified"
) -> ReindexStrategy:
    # 1. New File Rule: If we have no record of it, we must index it
    if not db_record:
        return ReindexStrategy.FULL_INDEX

    # 2. Deletion Rule: If it's in our DB but gone from disk, purge it [cite: 161]
    if not os.path.exists(file_path):
        return ReindexStrategy.PURGE

    # 3. Efficiency Rule: Compare content hash to avoid duplicate work [cite: 167]
    current_mtime = os.path.getmtime(file_path)
    if current_mtime <= db_record.get("last_modified_timestamp", 0):
        return ReindexStrategy.SKIP

    current_hash = calculate_file_hash(file_path)
    if current_hash == db_record.get("file_hash"):
        return ReindexStrategy.METADATA_UPDATE

    return ReindexStrategy.FULL_INDEX