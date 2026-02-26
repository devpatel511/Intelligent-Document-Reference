"""Configuration for the storage-optimized RAG ingestion pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RAGPipelineConfig:
    """Configurable parameters for the RAG ingestion pipeline."""

    # --- File ingestion ---
    supported_extensions: tuple[str, ...] = (".pdf", ".txt", ".md")
    """File types to ingest. PDF, TXT, Markdown."""

    exclude_patterns: tuple[str, ...] = (
        "**/node_modules/**",
        "**/.git/**",
        "**/__pycache__/**",
        "**/*.pyc",
    )
    """Glob patterns to exclude from crawling."""

    max_file_size_mb: float = 50.0
    """Skip files larger than this (MB)."""

    # --- Text preprocessing ---
    remove_boilerplate: bool = True
    """Remove headers, footers, TOC, copyright."""

    # --- Structural + semantic chunking ---
    min_chunk_tokens: int = 300
    max_chunk_tokens: int = 700
    """Target chunk size in tokens (structural chunking)."""

    overlap_tokens: int = 50
    """Overlap between adjacent chunks. ≤10% of max recommended."""

    max_overlap_ratio: float = 0.10
    """Max overlap as fraction of chunk size. Default 10%."""

    # --- Information density filtering ---
    min_tokens_density: int = 50
    """Minimum tokens to keep a chunk."""

    min_content_word_ratio: float = 0.35
    """Min ratio of content words (non-stopwords) to total words."""

    tfidf_novelty_threshold: float = 0.0
    """Optional TF-IDF novelty threshold (0 = disabled)."""

    density_filter_enabled: bool = True

    # --- Near-duplicate removal ---
    dedup_similarity_threshold: float = 0.95
    """Remove chunks with cosine similarity > this within same doc."""

    dedup_enabled: bool = True

    # --- Optional semantic merging ---
    semantic_merge_enabled: bool = False
    """Merge adjacent similar chunks to reduce vector count."""

    merge_similarity_threshold: float = 0.85
    """Merge chunks with similarity >= this."""

    merge_max_tokens: int = 1200
    """Max tokens after merge."""

    # --- Embedding ---
    embedding_dimension: int = 384
    """384 = smaller index, 768 = better recall. Tradeoff: 384 ~4x less storage."""

    embedding_batch_size: int = 32
    """Batch size for embedding API calls."""

    # --- Index storage ---
    use_faiss: bool = False
    """Use FAISS instead of sqlite-vec (optional, for larger corpora)."""

    faiss_index_path: Optional[Path] = None
    """Path to persist FAISS index."""

    # --- Logging ---
    log_chunks_generated: bool = True
    log_chunks_filtered_noise: bool = True
    log_chunks_filtered_dedup: bool = True
    log_final_vector_count: bool = True
