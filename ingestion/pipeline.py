"""Ingestion pipeline: input -> parse -> preprocess -> semantic chunk -> output chunks.

Provides a callable API for the full flow up to chunk production.
Storage and embedding are handled separately downstream.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from ingestion.chunking import chunk_document
from ingestion.config import IngestionConfig
from ingestion.models import BlockType, FileMetadata, StructuredDocument
from ingestion.orchestrator import parse_and_prepare
from ingestion.parser import get_input_handler


@dataclass
class IngestionResult:
    """Result of running the ingestion pipeline on a single input."""

    source_id: str
    """Identifier of the source (path, stream id, etc.)."""

    chunks: list[dict[str, Any]]
    """Chunks to store. Each dict has chunk_id, chunk_index, start_offset, end_offset, text_content."""

    document: StructuredDocument
    """Preprocessed structured document (blocks) for traceability."""

    block_count: int = field(init=False)
    chunk_count: int = field(init=False)
    file_metadata: Optional[FileMetadata] = None

    def __post_init__(self) -> None:
        self.block_count = len(self.document.blocks)
        self.chunk_count = len(self.chunks)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging or API responses."""
        return {
            "source_id": self.source_id,
            "block_count": self.block_count,
            "chunk_count": self.chunk_count,
            "chunks": self.chunks,
            "file_metadata": self.file_metadata.to_dict() if self.file_metadata else None,
        }


@dataclass
class PipelineConfig:
    """Configuration for the ingestion pipeline flow.

    Wraps IngestionConfig and adds chunker-specific settings.
    Ingestion always outputs final selected chunks (ready for vector DB).
    """

    ingestion: IngestionConfig = field(default_factory=IngestionConfig)

    # Chunker: block merging (used when use_structural_chunking=False)
    min_block_chars: int = 500
    max_block_chars: int = 2500

    # Chunker: store heuristic
    min_chars_store: int = 30
    max_chars_store: int = 30_000
    min_tokens_store: int = 5
    max_tokens_store: int = 8000
    skip_boilerplate: bool = True
    store_block_types: Optional[tuple[BlockType, ...]] = None
    skip_block_types: tuple[BlockType, ...] = ()

    # --- RAG-style path: structural chunking + density filter → final chunks ---
    use_structural_chunking: bool = False
    """If True, use token-based structural chunking (300-700) + optional density filter."""
    min_chunk_tokens: int = 300
    max_chunk_tokens: int = 700
    overlap_tokens: int = 50
    max_overlap_ratio: float = 0.10
    remove_boilerplate: bool = False
    """Remove headers/footers, TOC, copyright (RAG-style)."""
    density_filter_enabled: bool = False
    min_tokens_density: int = 50
    min_content_word_ratio: float = 0.35

    @classmethod
    def from_ingestion_config(cls, config: IngestionConfig) -> "PipelineConfig":
        """Build from IngestionConfig, inheriting PDF block sizes."""
        return cls(
            ingestion=config,
            min_block_chars=config.pdf_min_block_chars,
            max_block_chars=config.pdf_max_block_chars,
        )


def _apply_boilerplate_to_document(document: StructuredDocument) -> StructuredDocument:
    """Apply RAG-style boilerplate removal to block contents."""
    from ingestion.models import ContentBlock
    from rag.boilerplate import remove_boilerplate
    new_blocks = []
    for b in document.blocks:
        cleaned = remove_boilerplate(b.content)
        if cleaned:
            new_blocks.append(
                ContentBlock(
                    content=cleaned,
                    block_type=b.block_type,
                    source_modality=b.source_modality,
                    metadata=b.metadata,
                )
            )
    return StructuredDocument(
        source_id=document.source_id,
        blocks=new_blocks,
        source_modality=document.source_modality,
        file_metadata=document.file_metadata,
    )


def _structural_chunk_and_filter(
    document: StructuredDocument,
    config: PipelineConfig,
) -> list[dict[str, Any]]:
    """Produce final selected chunks via structural chunking + density filter."""
    from rag.chunking import structural_chunk_document
    from rag.density_filter import filter_by_density

    chunks = structural_chunk_document(
        document,
        min_tokens=config.min_chunk_tokens,
        max_tokens=config.max_chunk_tokens,
        overlap_tokens=config.overlap_tokens,
        max_overlap_ratio=config.max_overlap_ratio,
    )
    if config.density_filter_enabled:
        chunks = filter_by_density(
            chunks,
            min_tokens=config.min_tokens_density,
            min_content_word_ratio=config.min_content_word_ratio,
        )
    # Normalize to same chunk dict format as chunk_document (vector DB ready)
    return [
        {
            "chunk_id": c.chunk_id,
            "chunk_index": i,
            "start_offset": c.start_offset,
            "end_offset": c.end_offset,
            "text_content": c.text,
        }
        for i, c in enumerate(chunks)
    ]


class IngestionPipeline:
    """Ingestion pipeline: input -> parse -> preprocess -> chunk/filter -> final selected chunks."""

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        """Initialize with optional config. Uses defaults if None."""
        self.config = config or PipelineConfig()

    def ingest(
        self,
        source: Union[str, Path, BinaryIO],
        *,
        modality: Optional[str] = None,
        base_path: Optional[Path] = None,
    ) -> IngestionResult:
        """Run the pipeline and return final selected chunks (ready for vector DB).

        Args:
            source: File path, Path, or binary stream.
            modality: Optional override (pdf, image, code, text). Inferred from extension if omitted.
            base_path: Optional base path for relative file_metadata.

        Returns:
            IngestionResult with final selected chunks (chunk_id, chunk_index, start_offset, end_offset, text_content).
        """
        handler = get_input_handler(source, modality=modality)
        document = parse_and_prepare(
            handler,
            source,
            config=self.config.ingestion,
            base_path=base_path,
        )

        if self.config.use_structural_chunking:
            if self.config.remove_boilerplate:
                document = _apply_boilerplate_to_document(document)
            chunks = _structural_chunk_and_filter(document, self.config)
        else:
            chunks = chunk_document(
                document,
                min_block_chars=self.config.min_block_chars,
                max_block_chars=self.config.max_block_chars,
                min_chars_store=self.config.min_chars_store,
                max_chars_store=self.config.max_chars_store,
                min_tokens_store=self.config.min_tokens_store,
                max_tokens_store=self.config.max_tokens_store,
                skip_boilerplate=self.config.skip_boilerplate,
                store_block_types=self.config.store_block_types,
                skip_block_types=self.config.skip_block_types,
            )

        return IngestionResult(
            source_id=document.source_id,
            chunks=chunks,
            document=document,
            file_metadata=document.file_metadata,
        )


def run_index(path: str, ctx=None) -> None:
    """Index a file or directory. Uses ingestion for final selected chunks, then RAG to embed and store.

    - Ingestion produces final chunks (parse -> preprocess -> chunk -> filter).
    - RAG pipeline embeds those chunks, optionally deduplicates, and stores to vector DB.
    """
    from pathlib import Path
    from rag import run_rag_ingestion
    from rag.config import RAGPipelineConfig

    p = Path(path).resolve()
    if not p.exists():
        return
    db = getattr(ctx, "db", None) or (getattr(ctx, "unified_db", None) if ctx else None)
    embedder = getattr(ctx, "embedder", None) if ctx else None
    config = getattr(ctx, "rag_config", None) or RAGPipelineConfig()
    if p.is_file():
        from rag.crawler import DiscoveredFile
        ext = p.suffix.lower()
        if ext not in config.supported_extensions:
            return
        try:
            stat = p.stat()
            discovered = DiscoveredFile(
                path=p,
                file_name=p.name,
                extension=ext,
                size_bytes=stat.st_size,
                modified_timestamp=stat.st_mtime,
            )
            run_rag_ingestion(
                p.parent,
                config=config,
                db=db,
                embedder=embedder,
                files_override=[discovered],
            )
        except Exception:
            pass
    else:
        run_rag_ingestion(p, config=config, db=db, embedder=embedder)


def ingest(
    source: Union[str, Path, BinaryIO],
    *,
    config: Optional[PipelineConfig] = None,
    modality: Optional[str] = None,
    base_path: Optional[Path] = None,
) -> IngestionResult:
    """Convenience function: run the pipeline and return chunks.

    Args:
        source: File path, Path, or binary stream.
        config: Optional PipelineConfig. Uses defaults if None.
        modality: Optional override for input type.
        base_path: Optional base path for file metadata.

    Returns:
        IngestionResult with chunks.
    """
    pipeline = IngestionPipeline(config=config)
    return pipeline.ingest(source, modality=modality, base_path=base_path)
