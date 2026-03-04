"""Citation formatting helpers."""

from typing import Any, Dict, List


def format_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique citations from retrieved chunks.

    Args:
        chunks: List of chunk dicts returned by search_with_metadata,
                each containing at least 'file_path' and optionally 'distance'.

    Returns:
        Deduplicated list of citation dicts with file_path and relevance score.
    """
    seen = set()
    citations: List[Dict[str, Any]] = []
    for chunk in chunks:
        path = chunk.get("file_path", "unknown")
        if path not in seen:
            seen.add(path)
            citations.append(
                {
                    "file_path": path,
                    "relevance": round(1.0 - chunk.get("distance", 0.0), 4),
                }
            )
    return citations
