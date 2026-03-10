import os
from ingestion.change_detector import ReindexStrategy, determine_strategy

def test_new_file_strategy(tmp_path):
    """Verify that a file not in DB triggers a full index."""
    # Create a unique sub-directory for this specific test case
    test_dir = tmp_path / "change_detector_test"
    test_dir.mkdir()
    
    f = test_dir / "some_new_file.txt"
    f.write_text("new file content")

    # Now that the file exists in an isolated path, it bypasses the PURGE check
    assert determine_strategy(str(f), None) == ReindexStrategy.FULL_INDEX

def test_identical_file_strategy(tmp_path):
    """Verify that identical content returns SKIP or METADATA_UPDATE."""
    # Create a unique sub-directory to avoid any shared state
    test_dir = tmp_path / "identical_test"
    test_dir.mkdir()
    
    f = test_dir / "test.txt"
    f.write_text("content")

    # Mock DB record with same hash and future timestamp
    db_record = {
        "file_hash": "ed7002b479e9ac567e5029a696a744e66bdc3a272051214c519faef045505102",
        "last_modified_timestamp": os.path.getmtime(f) + 10,  # Future mtime to trigger SKIP
    }

    # If mtime is newer in DB, it should SKIP regardless of content
    assert determine_strategy(str(f), db_record) == ReindexStrategy.SKIP