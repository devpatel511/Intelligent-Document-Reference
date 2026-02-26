"""Storage-optimized local RAG ingestion pipeline.

Modular pipeline: crawl → parse → preprocess → chunk → density filter →
dedup → (optional merge) → embed → index.
"""

from rag.config import RAGPipelineConfig
from rag.pipeline import RAGPipeline, run_rag_ingestion

__all__ = [
    "RAGPipelineConfig",
    "RAGPipeline",
    "run_rag_ingestion",
]
