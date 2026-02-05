import os
import uuid

from backend.database import UnifiedDatabase


def simple_test() -> None:
    """Run a simple integration test for the UnifiedDatabase module.

    This test:
    1. Initializes the database.
    2. Registers a file.
    3. Adds a document chunk and its vector.
    4. Searches for the vector and verifies the result.
    """
    db_path = "test_unified_integration.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    print(f"Initializing UnifiedDatabase at {db_path}...")
    db = UnifiedDatabase(db_path)

    # 1. Register File
    print("Registering file...")
    file_id = db.register_file("docs/intro.txt", "hash123", 1024, 0.0)
    print(f"File ID: {file_id}")

    # 2. Create Version
    version_id = db.create_version(file_id, "v1_hash")

    # 3. Add Document (Chunks + Vectors)
    print("Adding chunks and vectors...")
    chunk_id = str(uuid.uuid4())

    chunks = [
        {
            "id": chunk_id,
            "chunk_index": 0,
            "start_offset": 0,
            "end_offset": 100,
            "text_content": "Hello world this is a test chunk.",
        }
    ]

    # Fake vector (384 dims)
    fake_vec = [0.1] * 384

    db.add_document(file_id, version_id, chunks, [fake_vec])
    print("Document inserted.")

    # 4. Search
    print("Searching vector...")
    results = db.search(fake_vec, limit=1)
    print("Results:", results)

    # Validate
    assert len(results) == 1
    # rowid might be 1.
    assert results[0]["chunk_id"] == chunk_id
    assert results[0]["text_content"] == "Hello world this is a test chunk."

    print("Search verification passed.")

    if os.path.exists(db_path):
        os.remove(db_path)
    print("\nTest Complete.")


if __name__ == "__main__":
    simple_test()
