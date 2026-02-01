from backend.database.metadata import MetadataManager
from backend.vectordb.factory import get_vector_db
import uuid

def simple_test():
    print("Initializing Metadata Store...")
    meta_db = MetadataManager("test_metadata.db")
    
    # Register a fake file
    file_id = meta_db.register_file("docs/intro.txt", "hash123", 1024, 0.0)
    print(f"Registered file with ID: {file_id}")
    
    # Create valid fake chunks for Metadata DB
    chunk_id = str(uuid.uuid4())
    chunks = [{
        "id": chunk_id,
        "file_id": file_id,
        "version_id": None,
        "chunk_index": 0,
        "start_offset": 0,
        "end_offset": 100,
        "text_content": "Hello world this is a test chunk."
    }]
    meta_db.add_chunks(chunks)
    print("Metadata chunk inserted.")

    # Initialize Vector Store (SQLite)
    print("\nInitializing SQLite Vector Store...")
    vec_db = get_vector_db("sqlite", db_path="test_vectors.db")
    vec_db.initialize()
    
    # Create fake vector (384 dims)
    fake_vec = [0.1] * 384
    
    print("Inserting vector...")
    vec_db.add_chunks([fake_vec], [{"meta": "data"}], [chunk_id])
    
    print("Searching vector...")
    results = vec_db.search(fake_vec, limit=1)
    print("Results:", results)
    
    vec_db.close()
    print("\nTest Complete.")

if __name__ == "__main__":
    simple_test()
