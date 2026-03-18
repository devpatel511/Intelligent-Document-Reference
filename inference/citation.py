"""Citation formatting helpers."""

import os
import re
from typing import Any, Dict, List


def _query_terms(query: str) -> set[str]:
    terms = re.findall(r"[a-z0-9_\-.]+", (query or "").lower())
    return {t for t in terms if len(t) > 1}


def _path_terms(path: str) -> set[str]:
    lowered = path.lower().replace("\\", "/")
    components = [c for c in lowered.split("/") if c]
    out: set[str] = set()
    for comp in components:
        stem, ext = os.path.splitext(comp)
        out.update(re.findall(r"[a-z0-9_]+", stem))
        if ext:
            out.add(ext)
            out.add(ext.lstrip("."))

    base = os.path.basename(lowered)
    stem, ext = os.path.splitext(base)
    if ext:
        out.add(ext)
        out.add(ext.lstrip("."))
    return out


def _path_match_score(path: str, query: str, q_terms: set[str]) -> float:
    if not query:
        return 0.0
    lowered_query = query.lower()
    basename = os.path.basename(path).lower()
    score = 0.0
    if basename and basename in lowered_query:
        score += 1.0
    p_terms = _path_terms(path)
    overlap = len(q_terms & p_terms)
    if overlap > 0:
        score += min(1.0, 0.25 * overlap)
    return score


def format_citations(
    chunks: List[Dict[str, Any]], max_items: int = 3, query: str = ""
) -> List[Dict[str, Any]]:
    """Extract unique citations from retrieved chunks.

    Args:
        chunks: List of chunk dicts returned by search_with_metadata,
                each containing at least 'file_path' and optionally 'distance',
                'text_content', and 'chunk_index'.

    Returns:
        Deduplicated and ranked list of citation dicts matching frontend interface.
    """
    q_terms = _query_terms(query)

    # Group chunks by file path and keep strongest evidence per file.
    grouped: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        path = chunk.get("file_path", "unknown")
        raw_distance = chunk.get("distance", None)
        if raw_distance is None:
            distance = 1.0
        else:
            distance = float(raw_distance)
        lexical = float(chunk.get("lexical_score", 0.0))
        hybrid = float(chunk.get("hybrid_score", 0.0))
        semantic_score = max(0.0, 1.0 - distance)
        hybrid_score = min(1.0, hybrid * 10.0) if hybrid > 0.0 else 0.0
        score = max(semantic_score, hybrid_score)
        score += min(0.25, lexical * 0.02)

        path_match = _path_match_score(path, query, q_terms)
        if path_match > 0:
            score += min(0.45, 0.2 * path_match)

        existing = grouped.get(path)
        if existing is None or score > existing["_score"]:
            snippet = chunk.get("text_content", "")
            grouped[path] = {
                "file_path": path,
                "file_name": os.path.basename(path),
                "snippet": snippet[:300] if snippet else "",
                "relevance_score": round(min(score, 1.0), 4),
                "chunk_index": chunk.get("chunk_index", 0),
                "_score": score,
                "_path_match": path_match,
            }

    ranked = sorted(grouped.values(), key=lambda c: c["_score"], reverse=True)
    if ranked:
        best = ranked[0]["_score"]
        # Only force path-only citations when query clearly targets files/paths.
        lowered_query = (query or "").lower()
        path_intent = any(
            marker in lowered_query
            for marker in ("file", "directory", "folder", "path", "/", "\\")
        )

        if path_intent and any(c.get("_path_match", 0.0) > 0.0 for c in ranked):
            ranked = [c for c in ranked if c.get("_path_match", 0.0) > 0.0]
        else:
            threshold = max(0.12, best * 0.80)
            ranked = [c for c in ranked if c["_score"] >= threshold]

    trimmed = ranked[:max_items]
    for citation in trimmed:
        citation.pop("_score", None)
        citation.pop("_path_match", None)
    return trimmed
