"""Optional semantic merging: combine adjacent similar chunks to reduce vector count."""

from typing import List, Tuple

import numpy as np

from rag.chunking import RAGChunk


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def merge_adjacent_similar(
    chunks: List[RAGChunk],
    embeddings: List[List[float]],
    *,
    similarity_threshold: float = 0.85,
    max_tokens: int = 1200,
) -> Tuple[List[RAGChunk], List[List[float]]]:
    """Merge adjacent chunks with similarity >= threshold.

    Final chunk size may reach max_tokens. Reduces vector count.

    Args:
        chunks: Ordered chunks from document.
        embeddings: Corresponding embeddings.
        similarity_threshold: Merge if adjacent similarity >= this.
        max_tokens: Maximum tokens per merged chunk.

    Returns:
        (merged_chunks, merged_embeddings).
    """
    if len(chunks) != len(embeddings) or len(chunks) <= 1:
        return chunks, embeddings

    from ingestion.models import estimate_tokens
    import uuid

    merged_chunks: List[RAGChunk] = []
    merged_embs: List[List[float]] = []
    i = 0

    while i < len(chunks):
        acc_texts = [chunks[i].text]
        acc_tokens = estimate_tokens(chunks[i].text)
        j = i + 1
        last_emb = embeddings[i]

        while j < len(chunks):
            cand = chunks[j]
            cand_emb = embeddings[j]
            cand_tokens = estimate_tokens(cand.text)
            if acc_tokens + cand_tokens > max_tokens:
                break
            sim = _cosine_similarity(last_emb, cand_emb)
            if sim < similarity_threshold:
                break
            acc_texts.append(cand.text)
            acc_tokens += cand_tokens
            last_emb = cand_emb
            j += 1

        combined = "\n\n".join(acc_texts)
        first = chunks[i]
        merged_chunks.append(
            RAGChunk(
                chunk_id=str(uuid.uuid4()),
                text=combined,
                chunk_index=len(merged_chunks),
                start_offset=first.start_offset,
                end_offset=chunks[j - 1].end_offset if j > i else first.end_offset,
                token_count=acc_tokens,
                section_hierarchy=first.section_hierarchy,
                page_number=first.page_number,
                file_path=first.file_path,
            )
        )
        merged_embs.append(np.mean([embeddings[k] for k in range(i, j)], axis=0).tolist())
        i = j

    return merged_chunks, merged_embs
