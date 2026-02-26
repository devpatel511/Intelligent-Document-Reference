# Storage-Optimized Local RAG Ingestion Pipeline

Production-grade, storage-efficient ingestion for a filesystem-based RAG system. Optimizes for minimal disk usage, minimal RAM, reduced vector count, and high retrieval recall.

## Architecture

```
Crawl (PDF/TXT/MD) → Parse → Preprocess → Boilerplate removal →
Structural chunk (300-700 tokens, ≤10% overlap) →
Density filter → Embed → Near-duplicate removal →
[Optional: Semantic merge] → Index (sqlite-vec)
```

**Layers:**
- **File ingestion**: Recursive crawl, metadata (file_path, page numbers, section headers)
- **Text preprocessing**: Boilerplate removal (headers, footers, TOC, copyright)
- **Structural chunking**: Respects document structure, token targets, minimal overlap
- **Density filtering**: Min tokens, content-word ratio, optional TF-IDF novelty
- **Deduplication**: Cosine similarity > 0.95 → remove redundant chunks
- **Semantic merge** (optional): Merge adjacent similar chunks to reduce vector count
- **Embedding**: Configurable backend (Voyage, Ollama, sentence-transformers)
- **Storage**: sqlite-vec (or optional FAISS)

## Usage

```python
from pathlib import Path
from rag import run_rag_ingestion, RAGPipeline, RAGPipelineConfig
from db.unified import UnifiedDatabase

# One-shot
result = run_rag_ingestion(
    Path("./docs"),
    config=RAGPipelineConfig(min_chunk_tokens=300, max_chunk_tokens=700),
    db=UnifiedDatabase("local_search.db"),
)
print(result["final_vector_count"])

# With custom embedder (e.g. sentence-transformers for local)
from rag.embedding_adapter import get_local_embedder
embedder = get_local_embedder()
if embedder:
    result = run_rag_ingestion(Path("./docs"), embedder=embedder)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_chunk_tokens` | 300 | Min tokens per chunk |
| `max_chunk_tokens` | 700 | Max tokens per chunk |
| `overlap_tokens` | 50 | Overlap between chunks |
| `max_overlap_ratio` | 0.10 | Overlap ≤10% of chunk size |
| `min_tokens_density` | 50 | Min tokens after density filter |
| `min_content_word_ratio` | 0.35 | Min non-stopword ratio |
| `dedup_similarity_threshold` | 0.95 | Remove chunks with sim > this |
| `semantic_merge_enabled` | False | Merge adjacent similar chunks |
| `embedding_dimension` | 384 | 384 = smaller index, 768 = better recall |

**Embedding dimension tradeoff:**
- **384 dims**: ~4× less storage, slightly lower recall
- **768 dims**: Better recall, larger index

## Logging

When `log_chunks_generated`, `log_chunks_filtered_noise`, `log_chunks_filtered_dedup`, and `log_final_vector_count` are enabled (default), the pipeline logs:

- Chunks generated (before filters)
- Chunks removed as noise (density filter)
- Chunks removed as duplicates
- Final vector count

## Integration

The `run_index(path, ctx)` entry point in `ingestion.pipeline` delegates to this RAG pipeline. The job worker calls it with `job.file_path` and `ctx` (with `db`, optional `embedder`).
