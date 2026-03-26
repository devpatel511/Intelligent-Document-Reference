"""LRU in-memory retrieval cache with semantic similarity deduplication.

The cache stores past retrieved chunks and reuses them for semantically similar queries.
Uses cosine distance to detect similarity; backed by SQLite for durability.
"""

import json
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RetrievalCache:
    """LRU cache for retrieved chunks with semantic similarity lookup."""

    def __init__(self, db: Any, max_size: int = 100, similarity_threshold: float = 0.1):
        """Initialize retrieval cache.

        Args:
            db: UnifiedDatabase instance for persistence.
            max_size: Maximum number of cached queries (LRU eviction if exceeded).
            similarity_threshold: Cosine distance threshold for cache hits (0-1, lower = more similar).
        """
        self.db = db
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold

        # In-memory LRU cache: query_embedding_hash -> {embedding, chunks, timestamp}
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def lookup(
        self, query_embedding: np.ndarray, similarity_threshold: Optional[float] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Look up cached chunks by semantic similarity to query embedding.

        Args:
            query_embedding: Query embedding vector (1D numpy array).
            similarity_threshold: Override default threshold for this lookup.

        Returns:
            List of cached chunks if similar query found; None otherwise.
        """
        if not self._cache:
            return None

        threshold = similarity_threshold or self.similarity_threshold

        # Compute distances to all cached embeddings using NumPy
        cached_embeddings = np.array(
            [entry["embedding"] for entry in self._cache.values()]
        )

        # Normalize embeddings for cosine distance
        query_normalized = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        cached_normalized = cached_embeddings / (
            np.linalg.norm(cached_embeddings, axis=1, keepdims=True) + 1e-8
        )

        # Compute distances as 1 - cosine_similarity
        similarities = np.dot(cached_normalized, query_normalized)
        distances = 1 - similarities

        # Find closest match
        min_idx = np.argmin(distances)
        min_distance = distances[min_idx]

        if min_distance < threshold:
            # Cache hit: move to end (most recently used) and return
            query_key = list(self._cache.keys())[min_idx]
            entry = self._cache.pop(query_key)
            self._cache[query_key] = entry

            # Update last_accessed_at in DB
            try:
                conn = self.db._get_conn()
                try:
                    conn.execute(
                        "UPDATE retrieval_cache SET last_accessed_at = CURRENT_TIMESTAMP WHERE query_text = ?",
                        (entry["query_text"],),
                    )
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to update cache access time: {e}")
                finally:
                    conn.close()
            except Exception:
                pass

            logger.debug(
                f"Cache hit for query (distance={min_distance:.4f}) -> reusing {len(entry['chunks'])} chunks"
            )
            return entry["chunks"]

        logger.debug(f"Cache miss (closest distance={min_distance:.4f} > {threshold})")
        return None

    def add(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        chunks: List[Dict[str, Any]],
    ) -> None:
        """Add query and retrieved chunks to cache.

        Args:
            query_text: Original query string.
            query_embedding: Query embedding vector.
            chunks: List of retrieved chunk dicts.
        """
        # Enforce LRU eviction
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Create cache key (use query text hash for uniqueness)
        query_key = query_text[:100]  # First 100 chars as simple key

        # Store in-memory
        self._cache[query_key] = {
            "query_text": query_text,
            "embedding": query_embedding,
            "chunks": chunks,
            "timestamp": datetime.now(),
        }

        # Persist to DB
        self._persist_to_db(query_text, query_embedding, chunks)

    def clear(self) -> None:
        """Clear all cached entries (in-memory and DB)."""
        self._cache.clear()
        try:
            conn = self.db._get_conn()
            try:
                conn.execute("DELETE FROM retrieval_cache")
                conn.commit()
                logger.info("Retrieval cache cleared")
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to clear retrieval_cache table: {e}")

    def _evict_lru(self) -> None:
        """Remove the least recently used (oldest) entry from cache."""
        if self._cache:
            evicted_key, evicted_entry = self._cache.popitem(last=False)
            logger.debug(f"LRU eviction: removed query '{evicted_key[:50]}...'")

    def _persist_to_db(
        self, query_text: str, query_embedding: np.ndarray, chunks: List[Dict[str, Any]]
    ) -> None:
        """Persist cache entry to SQLite."""
        try:
            conn = self.db._get_conn()
            try:
                # Convert embedding to BLOB (numpy -> bytes)
                embedding_blob = query_embedding.astype(np.float32).tobytes()
                chunks_json = json.dumps(chunks)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO retrieval_cache 
                    (query_text, query_embedding, retrieved_chunks_json, created_at, last_accessed_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (query_text, embedding_blob, chunks_json),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to persist cache to DB: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        return {
            "cache_size": len(self._cache),
            "max_size": self.max_size,
        }
