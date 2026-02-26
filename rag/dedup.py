"""Near-duplicate removal: drop chunks with cosine similarity > threshold."""

from typing import Any, List, Tuple

import numpy as np

from rag.chunking import RAGChunk


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def remove_near_duplicates(
    chunks: List[RAGChunk],
    embeddings: List[List[float]],
    threshold: float = 0.95,
) -> Tuple[List[RAGChunk], List[List[float]]]:
    """Remove chunks with similarity > threshold within the same document.

    Keeps the first occurrence when duplicates are found.

    Args:
        chunks: Chunks from a single document.
        embeddings: Corresponding embeddings (same order).
        threshold: Remove chunk if similarity to any kept chunk > this.

    Returns:
        (filtered_chunks, filtered_embeddings)
    """
    if len(chunks) != len(embeddings) or not chunks:
        return chunks, embeddings

    kept_indices: List[int] = [0]
    for i in range(1, len(chunks)):
        emb_i = embeddings[i]
        is_dup = False
        for k in kept_indices:
            sim = _cosine_similarity(emb_i, embeddings[k])
            if sim > threshold:
                is_dup = True
                break
        if not is_dup:
            kept_indices.append(i)

    return (
        [chunks[i] for i in kept_indices],
        [embeddings[i] for i in kept_indices],
    )


def remove_near_duplicates_dicts(
    chunk_dicts: List[dict[str, Any]],
    embeddings: List[List[float]],
    threshold: float = 0.95,
) -> Tuple[List[dict[str, Any]], List[List[float]]]:
    """Remove chunk dicts with similarity > threshold. Keeps first occurrence."""
    if len(chunk_dicts) != len(embeddings) or not chunk_dicts:
        return chunk_dicts, embeddings
    kept_indices: List[int] = [0]
    for i in range(1, len(chunk_dicts)):
        emb_i = embeddings[i]
        is_dup = False
        for k in kept_indices:
            if _cosine_similarity(emb_i, embeddings[k]) > threshold:
                is_dup = True
                break
        if not is_dup:
            kept_indices.append(i)
    return (
        [chunk_dicts[i] for i in kept_indices],
        [embeddings[i] for i in kept_indices],
    )
