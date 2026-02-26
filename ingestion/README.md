# Ingestion Pipeline

The ingestion pipeline prepares file context into **final selected chunks** ready for the vector DB. It is the single place that decides which chunks to produce; downstream (e.g. RAG) only embeds and stores them.

## How It Works

```
Input (path/stream) → Parse → Preprocess → [Boilerplate] → Chunk → [Density filter] → Final selected chunks
```

1. **Parse**: Input is routed by extension or modality to the appropriate handler (`PDFInput`, `ImageInput`, `CodeInput`, `TextInput`). Raw content is extracted into a `StructuredDocument` with blocks (paragraphs, code blocks, headings, etc.).

2. **Preprocess**: Blocks are cleaned (OCR artifacts, whitespace normalization, encoding) while preserving metadata.

3. **Chunk** (one of two modes):
   - **Semantic (default)**: Blocks merged by size; heuristic keeps chunks (length, block type, boilerplate detection).
   - **Structural (RAG-style)**: Token-based chunking (300–700 tokens, ≤10% overlap), optional boilerplate removal, then density filter (min tokens, content-word ratio). Set `use_structural_chunking=True` on `PipelineConfig`.

4. **Output**: `IngestionResult.chunks` is always a list of chunk dicts (`chunk_id`, `chunk_index`, `start_offset`, `end_offset`, `text_content`) — the **final selected chunks** to send to embedding and the vector DB.

## Usage

```python
from ingestion import ingest, IngestionPipeline, IngestionResult, PipelineConfig

# One-shot: path, Path, or binary stream
result = ingest("path/to/file.txt")
print(result.chunk_count, result.chunks)

# With config
config = PipelineConfig(
    min_block_chars=0,
    max_block_chars=2500,
    min_chars_store=30,
    skip_boilerplate=True,
)
result = ingest("path/to/file.py", config=config)

# Instance for reuse (e.g. in a server or batch job)
pipeline = IngestionPipeline(config=config)
result = pipeline.ingest("path/to/doc.pdf", modality="pdf")

# Final selected chunks — ready for vector DB
for chunk in result.chunks:
    # chunk["chunk_id"], chunk["text_content"], etc.
    pass

# RAG-style: structural chunking + density filter (same output format)
config_rag = PipelineConfig(
    use_structural_chunking=True,
    min_chunk_tokens=300,
    max_chunk_tokens=700,
    remove_boilerplate=True,
    density_filter_enabled=True,
)
result = ingest("path/to/doc.pdf", config=config_rag)
```

### Supported Input Types

| Extension / Modality | Handler   |
|----------------------|-----------|
| `.pdf`               | PDFInput  |
| `.png`, `.jpg`, …    | ImageInput|
| `.py`, `.js`, `.md`, …| CodeInput |
| `.txt`, default      | TextInput |

Override with `modality="pdf"`, `"image"`, `"code"`, or `"text"`.

## Configuration

### PipelineConfig

- **Block merging** (semantic path): `min_block_chars`, `max_block_chars`, and store heuristic: `min_chars_store`, `max_chars_store`, `min_tokens_store`, `max_tokens_store`, `skip_boilerplate`, `store_block_types`, `skip_block_types`.
- **Structural path** (final chunks for RAG): `use_structural_chunking=True`, `min_chunk_tokens`, `max_chunk_tokens`, `overlap_tokens`, `max_overlap_ratio`, `remove_boilerplate`, `density_filter_enabled`, `min_tokens_density`, `min_content_word_ratio`.

### IngestionConfig (parsing)

- `pdf_min_block_chars`, `pdf_max_block_chars` — PDF block sizing.
- `ocr_enabled`, `llm_enabled`, etc. — for OCR and LLM-assisted extraction.

Use `PipelineConfig.from_ingestion_config(IngestionConfig())` to inherit PDF block sizes.

## Tests

### Run All Ingestion Pipeline Tests

Run from the project root:

```bash
pytest tests/unit/test_ingestion_pipeline_main.py -v -s
```

- `-v` — verbose (test names)
- `-s` — show print output (chunk counts, content previews, etc.)

Without `-s`, pytest captures stdout and you only see PASSED/FAILED. With `-s`, you see the actual output (chunk counts, content previews, etc.).

This runs all 20 tests (parsing, preprocessing, semantic chunking, pipeline API, and accuracy). Example output with `-s`:

```
============================= test session starts =============================
platform win32 -- Python 3.13.x, pytest-9.0.2, ...
cachedir: .pytest_cache
rootdir: C:\Users\sharatdev\Desktop\projects\Intelligent-Document-Reference-Winter2026
configfile: pyproject.toml
plugins: anyio-4.11.0
collecting ... collected 20 items

tests/unit/test_ingestion_pipeline_main.py::test_chunk_document_produces_storeable_chunks PASSED
tests/unit/test_ingestion_pipeline_main.py::test_code_input_parses_file PASSED
tests/unit/test_ingestion_pipeline_main.py::test_ingest_code_file_produces_code_chunks
  chunks=1, sample: ['def greet(name):\n    print("Hello", name)...']
PASSED
tests/unit/test_ingestion_pipeline_main.py::test_ingest_returns_valid_result_structure
  source_id='...sample.txt'
  block_count=1, chunk_count=1
PASSED
...
tests/unit/test_ingestion_pipeline_main.py::test_get_input_handler_selects_by_extension PASSED
...
tests/unit/test_ingestion_pipeline_main.py::test_ingest_filters_short_boilerplate
  block_count=1, chunk_count=0 (filtered: too short)
PASSED
...
tests/unit/test_ingestion_pipeline_main.py::test_ingest_sample_text_file
  sample.txt: chunks=1, preview: This is a sample plain text file for testing...
PASSED
...

============================= 20 passed in 0.18s ==============================
```

### Individual Test Files

You can also run the underlying modules separately (add `-s` to see print output):

```bash
pytest tests/unit/test_ingestion.py tests/unit/test_pipeline.py -v -s
```

#### Ingestion (`test_ingestion.py`)

| Test | Purpose |
|------|---------|
| `test_text_input_parses_file` | Text files parse to paragraph blocks |
| `test_code_input_parses_file` | Code files parse to code blocks |
| `test_get_input_handler_selects_by_extension` | Handler selection by extension |
| `test_preprocessing_normalizes_whitespace` | Preprocessing cleans and normalizes |
| `test_structured_document_serializable` | Document serialization |
| `test_chunk_document_produces_storeable_chunks` | Chunker merges blocks and applies heuristic |
| `test_should_store_chunk_heuristic` | Heuristic filters by length and boilerplate |

#### Pipeline (`test_pipeline.py`)

| Test | Purpose |
|------|---------|
| `test_ingest_returns_valid_result_structure` | Result has required fields |
| `test_ingest_chunks_have_required_schema` | Chunks have chunk_id, chunk_index, text_content, etc. |
| `test_ingest_result_to_dict_serializable` | Result is JSON-serializable |
| `test_ingest_text_file_produces_text_chunks` | Text input → text chunks |
| `test_ingest_code_file_produces_code_chunks` | Code input → code chunks |
| `test_ingest_filters_short_boilerplate` | Very short content filtered out |
| `test_ingest_filters_page_number_like_content` | Page-number style content filtered |
| `test_ingest_preserves_substantive_content` | Real content kept when mixed with short lines |
| `test_pipeline_instance_ingest` | `IngestionPipeline.ingest()` works |
| `test_pipeline_respects_config` | `PipelineConfig` affects behavior |
| `test_pipeline_modality_override` | `modality` forces input handler |
| `test_ingest_sample_text_file` | Runs on `ingestion/sample_files/text/sample.txt` |
| `test_ingest_sample_code_file` | Runs on `ingestion/sample_files/code/sample.py` |

### What the Tests Validate

- **Validity**: Result structure, chunk schema, serialization.
- **Accuracy**: Known inputs produce expected outputs (content preserved, boilerplate filtered).
