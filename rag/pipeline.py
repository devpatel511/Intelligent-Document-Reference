"""RAG pipeline: ingestion (final chunks) -> embed -> dedup -> store in vector DB.

Ingestion is the single source of final selected chunks; this module only
embeds them, optionally deduplicates, and persists to the vector DB.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Callable, List, Optional

from ingestion.pipeline import IngestionPipeline, PipelineConfig
from rag.config import RAGPipelineConfig
from rag.crawler import crawl_directory, DiscoveredFile
from rag.dedup import remove_near_duplicates_dicts
from rag.embedding_adapter import embed_texts_batched

logger = logging.getLogger(__name__)


def _rag_config_to_pipeline_config(cfg: RAGPipelineConfig) -> PipelineConfig:
    """Build ingestion PipelineConfig from RAG config so ingestion produces final chunks."""
    return PipelineConfig(
        use_structural_chunking=True,
        min_chunk_tokens=cfg.min_chunk_tokens,
        max_chunk_tokens=cfg.max_chunk_tokens,
        overlap_tokens=cfg.overlap_tokens,
        max_overlap_ratio=cfg.max_overlap_ratio,
        remove_boilerplate=cfg.remove_boilerplate,
        density_filter_enabled=cfg.density_filter_enabled,
        min_tokens_density=cfg.min_tokens_density,
        min_content_word_ratio=cfg.min_content_word_ratio,
    )


def run_rag_ingestion(
    root_path: Path,
    *,
    config: Optional[RAGPipelineConfig] = None,
    db: Optional[Any] = None,
    embedder: Optional[Callable[[List[str]], List[List[float]]]] = None,
    files_override: Optional[List] = None,
) -> dict[str, Any]:
    """Run RAG pipeline: get final chunks from ingestion -> embed -> dedup -> store.

    Ingestion produces the final selected chunks (structural chunking + density
    filter). This function only embeds them, optionally removes near-duplicates,
    and persists to the vector DB.

    Args:
        root_path: Directory to crawl for PDF, TXT, MD (or parent if files_override).
        config: RAG config. Drives ingestion PipelineConfig for final chunks.
        db: UnifiedDatabase for storage. If None, chunks/embeddings not persisted.
        embedder: Optional embedder. If None, uses embedding_adapter.
        files_override: If set, process only these DiscoveredFile items.

    Returns:
        Summary with chunks_generated, chunks_filtered_dedup, final_vector_count, chunks, embeddings.
    """
    cfg = config or RAGPipelineConfig()
    root_path = Path(root_path).resolve()
    pipeline_config = _rag_config_to_pipeline_config(cfg)
    ingestion_pipeline = IngestionPipeline(config=pipeline_config)

    total_chunks_generated = 0
    total_chunks_filtered_dedup = 0
    total_files_processed = 0
    all_chunks: List[dict[str, Any]] = []
    all_embeddings: List[List[float]] = []

    file_iter = files_override if files_override is not None else crawl_directory(root_path, cfg)

    for discovered in file_iter:
        total_files_processed += 1
        try:
            result = ingestion_pipeline.ingest(
                str(discovered.path),
                base_path=root_path,
            )
            chunks = result.chunks
            if not chunks:
                continue

            total_chunks_generated += len(chunks)
            texts = [c["text_content"] for c in chunks]

            if embedder:
                embeddings = embedder(texts)
            else:
                try:
                    embeddings = embed_texts_batched(
                        texts,
                        batch_size=cfg.embedding_batch_size,
                    )
                except RuntimeError as e:
                    logger.warning("Embedding skipped (%s), skipping vector store for this file", e)
                    embeddings = []

            if not embeddings or len(embeddings) != len(chunks):
                continue

            n_before_dedup = len(chunks)
            if cfg.dedup_enabled:
                chunks, embeddings = remove_near_duplicates_dicts(
                    chunks,
                    embeddings,
                    threshold=cfg.dedup_similarity_threshold,
                )
                total_chunks_filtered_dedup += n_before_dedup - len(chunks)

            for c in chunks:
                c["file_path"] = str(discovered.path)
                all_chunks.append(c)
            all_embeddings.extend(embeddings)

            if db and embeddings:
                file_hash = discovered.content_hash or hashlib.sha256(str(discovered.path).encode()).hexdigest()
                file_id = db.register_file(
                    str(discovered.path),
                    file_hash,
                    discovered.size_bytes,
                    discovered.modified_timestamp,
                )
                version_id = db.create_version(file_id, file_hash)
                chunk_dicts = [
                    {
                        "chunk_id": c["chunk_id"],
                        "chunk_index": i,
                        "start_offset": c["start_offset"],
                        "end_offset": c["end_offset"],
                        "text_content": c["text_content"],
                    }
                    for i, c in enumerate(chunks)
                ]
                db.add_document(file_id, version_id, chunk_dicts, embeddings)

        except Exception as e:
            logger.exception("Failed to process %s: %s", discovered.path, e)

    total_vectors = len(all_embeddings)
    if cfg.log_chunks_generated:
        logger.info("Chunks generated (final selected from ingestion): %d", total_chunks_generated)
    if cfg.log_chunks_filtered_dedup:
        logger.info("Chunks removed as duplicates: %d", total_chunks_filtered_dedup)
    if cfg.log_final_vector_count:
        logger.info("Final vector count: %d", total_vectors)

    return {
        "chunks_generated": total_chunks_generated,
        "chunks_filtered_dedup": total_chunks_filtered_dedup,
        "final_vector_count": total_vectors,
        "files_processed": total_files_processed,
        "chunks": all_chunks,
        "embeddings": all_embeddings,
    }


class RAGPipeline:
    """Convenience wrapper: ingestion (final chunks) -> embed -> dedup -> store."""

    def __init__(
        self,
        config: Optional[RAGPipelineConfig] = None,
        db: Optional[Any] = None,
        embedder: Optional[Callable[[List[str]], List[List[float]]]] = None,
    ):
        self.config = config or RAGPipelineConfig()
        self.db = db
        self.embedder = embedder

    def ingest(self, root_path: Path) -> dict[str, Any]:
        return run_rag_ingestion(
            root_path,
            config=self.config,
            db=self.db,
            embedder=self.embedder,
        )
