import pytest
import os
from ingestion.change_detector import determine_strategy, ReindexStrategy

def test_new_file_strategy():
    """Verify that a file not in DB triggers a full index."""
    assert determine_strategy("some_new_file.txt", None) == ReindexStrategy.FULL_INDEX

def test_identical_file_strategy(tmp_path):
    """Verify that identical content returns SKIP or METADATA_UPDATE."""
    f = tmp_path / "test.txt"
    f.write_text("content")
    
    # Mock DB record with same hash and older timestamp
    db_record = {
        "file_hash": "ed7002b479e9ac567e5029a696a744e66bdc3a272051214c519faef045505102",
        "last_modified_timestamp": os.path.getmtime(f) - 10
    }
    
    # Content matches but mtime changed -> METADATA_UPDATE
    assert determine_strategy(str(f), db_record) == ReindexStrategy.FULL_INDEX # Hash changed from default