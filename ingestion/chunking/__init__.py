"""Chunking package: build chunks from blocks and decide which to store."""

from ingestion.chunking.semantic import (
    CandidateChunk,
    chunk_document,
    should_store_chunk,
)

__all__ = [
    "CandidateChunk",
    "chunk_document",
    "should_store_chunk",
]
