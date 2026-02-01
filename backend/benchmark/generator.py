import random
import uuid
import numpy as np

def generate_dummy_data(count=1000, dim=384):
    """
    Generates 'count' random vectors and corresponding metadata.
    """
    vectors = np.random.rand(count, dim).astype(np.float32).tolist()
    ids = [str(uuid.uuid4()) for _ in range(count)]
    metadatas = [{"source": f"file_{i}.txt", "chunk": i} for i in range(count)]
    return vectors, metadatas, ids
