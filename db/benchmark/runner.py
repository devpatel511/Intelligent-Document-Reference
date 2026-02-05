import os
import time

import numpy as np

from backend.benchmark.generator import generate_dummy_data
from backend.database import UnifiedDatabase


def run_benchmark(count: int = 5000) -> None:
    """Run a performance benchmark on the UnifiedDatabase.

    Measures ingestion speed and query latency.

    Args:
        count: Number of dummy items to ingest and test. Defaults to 5000.
    """
    print("--- Benchmarking UnifiedSQLite ---")
    db_path = "bench_unified.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    db = UnifiedDatabase(db_path)

    # 1. Register ID
    file_id = db.register_file("bench.txt", "hash", 0, 0.0)
    version_id = db.create_version(file_id, "v1")

    # 2. Data Gen
    vectors, metas, ids = generate_dummy_data(count=count)

    chunks = []
    for i, mid in enumerate(ids):
        chunks.append({"id": mid, "text_content": f"Dummy content {i} - {metas[i]}"})

    # 3. Ingest Test
    start_time = time.time()
    db.add_document(file_id, version_id, chunks, vectors)
    ingest_duration = time.time() - start_time
    print(
        f"Ingestion ({count} items): {ingest_duration:.4f}s "
        f"({count/ingest_duration:.1f} items/s)"
    )

    # 4. Query Test
    query_vec = np.random.rand(384).tolist()
    start_time = time.time()
    for _ in range(50):  # 50 queries
        db.search(query_vec, limit=5)
    query_duration = time.time() - start_time
    avg_query_lat = (query_duration / 50) * 1000
    print(f"Query (avg of 50): {avg_query_lat:.2f}ms")


if __name__ == "__main__":
    run_benchmark()
