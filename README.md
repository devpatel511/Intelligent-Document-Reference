# Intelligent Document Reference

Local-first RAG system: ingest documents, embed with OpenAI/Voyage, and query them with citations. FastAPI backend + React/Vite frontend, SQLite with sqlite-vec for vector search.

## Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **uv** (recommended) — [docs.astral.sh/uv](https://docs.astral.sh/uv/)

## Quick Start

```bash
# One-command setup + launch
python3 app.py --setup --webui
```

This creates `.venv`, installs Python deps (uv if available, pip fallback), installs npm packages, builds the frontend, and starts the server at **http://127.0.0.1:8000**.

After the first setup, just run:

```bash
python3 app.py --webui
# or with uv:
uv run app.py --webui
```

## Manual Setup

```bash
uv sync                         # Python deps
cd ui && npm install && cd ..   # Frontend deps
cd ui && npm run build && cd .. # Build frontend
```

Then launch with `uv run app.py --webui` or `.venv/bin/python app.py --webui`.

## Development

```bash
python3 app.py --dev
```

Runs uvicorn with `--reload` on `:8000` and the Vite dev server on `:5173`. Open **http://localhost:5173**.

## Benchmarks

```bash
python3 app.py --benchmark                              # defaults
python3 app.py --benchmark local                        # local embed + local inference
python3 app.py --benchmark api                          # OpenAI API embed + inference
python3 app.py --benchmark gemini                       # Gemini embed + inference
python3 app.py --benchmark local --embed nomic-embed-text --model llama3.2
python3 app.py --benchmark local --embed embeddinggemma:latest --model deepseek-coder:6.7b --vlm qwen2.5vl:7b
python3 app.py --benchmark local --benchmark-dataset-id 13 --benchmark-runs 1 --no-graphs
python3 app.py --benchmark api --embed text-embedding-3-large --model gpt-4o-mini
python3 app.py --benchmark api --embed models/gemini-embedding-001 --model gemini-2.5-flash-lite
python3 app.py --benchmark --skip-indexing              # skip re-indexing
python3 app.py --benchmark --benchmark-config my.yaml
python3 app.py --benchmark --benchmark-runs 1 --no-graphs --benchmark-output results/
```

Benchmark mode bypasses the UI and runs the full ingestion -> chunk -> embed -> retrieve -> generate pipeline directly from benchmark YAML.
The benchmark runner now auto-probes the selected embedding model's default vector dimension and builds an isolated benchmark DB with that dimension to avoid embedding/index mismatches.
API keys can come from either saved UI settings or `.env` (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `VOYAGE_API_KEY`).
Benchmark mode forces `OCR_ENABLED=false`, so runs do not depend on Tesseract.
Use `--benchmark-dataset-id` to run one dataset at a time (for example `13` or `dataset13`). This scopes both indexing and prompt evaluation to that dataset for faster iterations.

The default benchmark YAML now supports `benchmark.dataset_suites`, which runs dataset folders sequentially (`dataset0` ... `dataset17`). For each dataset suite, prompts are auto-selected by dataset-relative expected paths and sampled by difficulty levels (`easy`, `medium`, `hard`) configured in YAML.

For local-only image ingestion (no cloud APIs), use a local multimodal inference model (for example `qwen2.5vl:7b`) as your inference model. The ingestion pipeline uses the active inference client for image-to-text (`describe_image`) when available, so local VLM models can replace OCR/API vision for image chunking.
If a non-vision local model is selected, ingestion logs a one-time warning and skips VLM image description.
For benchmark runs specifically, use `--vlm` to set a dedicated image-to-text model for ingestion while keeping `--model` for answer generation.

## Configuration

Create a `.env` file in the project root:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key (embeddings + inference) |
| `VOYAGE_API_KEY` | — | Voyage AI key (embeddings) |
| `GEMINI_API_KEY` | — | Google Gemini key |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint for local models |
| `EMBEDDING_DIMENSION` | `3072` | Vector dimension (must match model) |
| `OCR_ENABLED` | `false` | Enable Tesseract OCR for images |

YAML configs in `config/`: `models.yaml` (provider model IDs), `paths.yaml` (watch/exclude dirs), `file_indexing.yaml` (inclusion/exclusion rules, auto-managed by Settings UI).

## CLI Reference

```
python3 app.py [OPTIONS]

--setup               Install deps + build frontend
--webui               Launch server (auto-builds if needed)
--dev                 Dev mode: backend (hot-reload) + Vite HMR
--host HOST           Bind address (default: 127.0.0.1)
--port PORT           Bind port (default: 8000)
--benchmark           Run evaluation suite
					  Optional preset: default|local|api|gemini
--embed MODEL         Override embedding model for benchmark run
--model MODEL         Override inference model for benchmark run
--vlm MODEL           Optional VLM model for benchmark image-to-text ingestion
--benchmark-config F  Benchmark YAML config
--benchmark-dataset D Override dataset path
--benchmark-dataset-id X Scope benchmark to one dataset + matching prompts (e.g. 13)
--benchmark-output O  Override output directory
--benchmark-runs N    Override runs per query
--no-graphs           Skip graph generation
--skip-indexing       Query existing index only
```

## Testing

```bash
uv sync --group dev   # install test deps
pytest                # all tests
pytest tests/unit/    # unit only
pytest tests/e2e/     # end-to-end
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Use `.venv/bin/python app.py --webui` or `uv run app.py --webui` |
| Port 8000 in use | `python3 app.py --webui --port 8080` |
| Frontend not loading | `cd ui && npm run build` |
| Folder picker unavailable | See [docs/TKINTER_SETUP.md](docs/TKINTER_SETUP.md) |
| Stale venv | `rm -rf .venv && python3 app.py --setup` |
