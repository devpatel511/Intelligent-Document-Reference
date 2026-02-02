import time
import os
import shutil
import numpy as np
from backend.vectordb.factory import get_vector_db
from backend.benchmark.generator import generate_dummy_data


def run_benchmark(db_type: str, count=5000):  # ChromaDB has a batch limit of 5461
    print(f"--- Benchmarking {db_type.upper()} ---")

    # 1. Setup & Cleanup
    db_path = f"bench_{db_type}.db"
    chroma_path = f"bench_chroma_{db_type}"

    # Clean previous run
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    # Initialize
    if db_type == "sqlite":
        db = get_vector_db("sqlite", db_path=db_path)
    else:
        db = get_vector_db("chroma", persist_path=chroma_path)

    db.initialize()

    # 2. Data Gen
    vectors, metas, ids = generate_dummy_data(count=count)

    # 3. Ingest Test
    start_time = time.time()
    db.add_chunks(vectors, metas, ids)
    ingest_duration = time.time() - start_time
    print(
        f"Ingestion ({count} items): {ingest_duration:.4f}s ({count/ingest_duration:.1f} items/s)"
    )

    # 4. Query Test
    query_vec = np.random.rand(384).tolist()
    start_time = time.time()
    for _ in range(50):  # 50 queries
        db.search(query_vec, limit=5)
    query_duration = time.time() - start_time
    avg_query_lat = (query_duration / 50) * 1000
    print(f"Query (avg of 50): {avg_query_lat:.2f}ms")

    db.close()

    # 5. Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)


if __name__ == "__main__":
    run_benchmark("sqlite")
    print("\n")
    run_benchmark("chroma")
