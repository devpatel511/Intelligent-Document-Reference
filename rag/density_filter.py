"""Information density filtering: remove low-signal chunks without harming recall."""

from collections import Counter
from typing import List, Set

from ingestion.models import estimate_tokens

from rag.chunking import RAGChunk


# Common stopwords (English) - minimal set for content-word ratio
_STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "it", "its", "they", "them", "their",
    "i", "you", "he", "she", "we", "what", "which", "who", "when",
    "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just",
}


def _content_word_ratio(text: str) -> float:
    """Ratio of non-stopword tokens to total tokens."""
    words = text.lower().split()
    if not words:
        return 0.0
    content = sum(1 for w in words if w not in _STOPWORDS)
    return content / len(words)


def _tfidf_novelty(chunk: RAGChunk, all_chunks: List[RAGChunk]) -> float:
    """Simple TF-IDF inspired novelty: rare terms in doc get higher score.

    Returns a value in [0, 1] where higher = more novel/unique.
    """
    if not all_chunks:
        return 1.0
    doc_terms: Counter = Counter()
    for c in all_chunks:
        for w in c.text.lower().split():
            if w not in _STOPWORDS and len(w) > 2:
                doc_terms[w] += 1
    chunk_terms = [w for w in chunk.text.lower().split() if w not in _STOPWORDS and len(w) > 2]
    if not chunk_terms:
        return 0.0
    total_docs = len(all_chunks)
    novelty = sum(1.0 / (1 + doc_terms.get(w, 0)) for w in chunk_terms) / len(chunk_terms)
    return min(1.0, novelty)


def filter_by_density(
    chunks: List[RAGChunk],
    *,
    min_tokens: int = 50,
    min_content_word_ratio: float = 0.35,
    tfidf_threshold: float = 0.0,
    use_tfidf: bool = False,
) -> List[RAGChunk]:
    """Remove low-information chunks by density heuristics.

    Args:
        chunks: Candidate chunks from same document.
        min_tokens: Minimum token count.
        min_content_word_ratio: Minimum ratio of content words to total.
        tfidf_threshold: Minimum TF-IDF novelty (if use_tfidf).
        use_tfidf: Whether to apply TF-IDF novelty filter.

    Returns:
        Filtered list of chunks.
    """
    out: List[RAGChunk] = []
    for c in chunks:
        if estimate_tokens(c.text) < min_tokens:
            continue
        if _content_word_ratio(c.text) < min_content_word_ratio:
            continue
        if use_tfidf and tfidf_threshold > 0:
            nov = _tfidf_novelty(c, chunks)
            if nov < tfidf_threshold:
                continue
        out.append(c)
    return out
