"""Ingestion pipeline package.

Document ingestion and parsing pipeline that prepares heterogeneous inputs
(PDF, images, code, plain text) for a semantic chunking engine.

Public entry point: parse_and_prepare(document, source, ...)
"""

from ingestion.config import IngestionConfig
from ingestion.models import (
    BlockMetadata,
    BlockType,
    ContentBlock,
    ExtractionMethod,
    FileMetadata,
    SourceModality,
    StructuredDocument,
    estimate_tokens,
    file_metadata_from_path,
)
from ingestion.ocr import OCRProvider, OCRResult, TesseractOCRProvider
from ingestion.orchestrator import parse_and_prepare, parse_and_prepare_batch
from ingestion.parser import (
    CodeInput,
    ImageInput,
    InputDocument,
    InputSource,
    PDFInput,
    TextInput,
    get_input_handler,
)
from ingestion.preprocessing import preprocess
from ingestion.chunking import chunk_document, should_store_chunk
from ingestion.pipeline import (
    IngestionPipeline,
    IngestionResult,
    PipelineConfig,
    ingest,
)

__all__ = [
    "parse_and_prepare",
    "parse_and_prepare_batch",
    "get_input_handler",
    "preprocess",
    "IngestionConfig",
    "InputDocument",
    "InputSource",
    "PDFInput",
    "ImageInput",
    "TextInput",
    "CodeInput",
    "OCRProvider",
    "OCRResult",
    "TesseractOCRProvider",
    "StructuredDocument",
    "ContentBlock",
    "BlockMetadata",
    "FileMetadata",
    "BlockType",
    "ExtractionMethod",
    "SourceModality",
    "file_metadata_from_path",
    "estimate_tokens",
    "chunk_document",
    "should_store_chunk",
    "IngestionPipeline",
    "IngestionResult",
    "PipelineConfig",
    "ingest",
]
