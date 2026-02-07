# Local-first Intelligent Document Reference — Architecture

A local-first RAG (Retrieval-Augmented Generation) system with an intelligent document reference interface.

## Quick Start

### Option 1: Automated Setup (Recommended)

The easiest way to get started is using the automated setup:

```bash
python3 app.py --setup --webui
```

This will:
- Create a Python virtual environment
- Install all Python dependencies
- Install Node.js dependencies
- Build the frontend
- Launch the web UI

### Option 2: Manual Setup

If you prefer to set up manually, see the [Installation](#installation) section below.

## Installation

### Prerequisites

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
- **Git** (optional, for cloning the repository)

### Automated Setup

Run the setup script to automatically configure everything:

```bash
python3 app.py --setup
```

This will:
1. Check for required tools (Python, Node.js, npm)
2. Create a Python virtual environment (`.venv`)
3. Install Python dependencies (using uv if available, otherwise pip)
4. Install Node.js dependencies in the `ui/` directory
5. Build the frontend application

After setup, you can launch the application with:

```bash
python3 app.py --webui
```

### Manual Setup

#### 1. Python Environment Setup

Create and activate a virtual environment:

**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 2. Install Python Dependencies

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install .
```

#### 3. Install Node.js Dependencies

```bash
cd ui
npm install
cd ..
```

#### 4. Build Frontend

```bash
cd ui
npm run build
cd ..
```

## Running the Application

### Launch Web UI

After setup, launch the web interface:

```bash
python3 app.py --webui
```

The application will be available at `http://127.0.0.1:8000`

### Custom Host/Port

You can specify a custom host and port:

```bash
python3 app.py --webui --host 0.0.0.0 --port 8080
```

### Command Line Options

```bash
python3 app.py [OPTIONS]

Options:
  --setup          Set up the environment (install dependencies, build frontend)
  --webui          Launch the web UI with backend server
  --host HOST      Host to bind the server to (default: 127.0.0.1)
  --port PORT      Port to bind the server to (default: 8000)
  -h, --help       Show help message
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (you can copy from `.env.example` if it exists) to configure:

- `DATABASE_URL`: Database connection string (default: `sqlite:///./data/metadata.db`)
- `VECTOR_DB_PATH`: Path to vector database (default: `./data/vectorstore`)
- `OLLAMA_URL`: Ollama API URL (default: `http://localhost:11434`)
- `DOCUMENT_PATH`: Path to documents directory for file indexing (default: current directory)

### API Configuration

The backend API runs on `http://127.0.0.1:8000` by default. You can change the host and port using command-line arguments.

## Troubleshooting

### Python Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
# Remove and recreate the virtual environment
rm -rf .venv
python3 app.py --setup
```

### Node.js Dependencies Issues

If frontend dependencies fail to install:

```bash
cd ui
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
```

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
python3 app.py --webui --port 8080
```

### Frontend Not Loading

If the frontend doesn't load:
1. Check that the frontend is built: `ls ui/dist`
2. Rebuild if needed: `cd ui && npm run build && cd ..`
3. Check browser console for errors

## Development

### Running in Development Mode

For frontend development with hot-reload:

```bash
cd ui
npm run dev
```

This will start the Vite dev server (typically on port 5173).

For backend development, you can run the FastAPI server directly:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Project Structure

## Final Directory Structure

```
├── app.py
├── README.md
├── pyproject.toml
├── .env.example
├── config/
│   ├── settings.py
│   ├── models.yaml
│   └── paths.yaml
├── core/
│   ├── bootstrap.py
│   ├── wiring.py
│   ├── lifecycle.py
│   └── context.py
├── model_clients/
│   ├── base.py
│   ├── openai_client.py
│   ├── google_client.py
│   ├── ollama_client.py
│   ├── registry.py
│   └── errors.py
├── embeddings/
│   ├── base.py
│   ├── router.py
│   └── embedder.py
├── inference/
│   ├── retriever.py
│   ├── rag.py
│   ├── citation.py
│   ├── router.py
│   └── responder.py
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── routes_chat.py
│   │   ├── routes_files.py
│   │   ├── routes_jobs.py
│   │   └── routes_settings.py
│   ├── deps.py
│   └── schemas.py
├── ingestion/
│   ├── extractors/
│   ├── chunking/
│   ├── pipeline.py
│   └── indexer.py
├── db/
│   ├── metadata.py
│   ├── vectorstore.py
│   ├── settings_store.py
│   ├── schema.sql
│   └── migrations/
├── watcher/
│   ├── watcher.py
│   ├── debounce.py
│   └── events.py
├── jobs/
│   ├── queue.py
│   ├── scheduler.py
│   ├── worker.py
│   └── state.py
├── ui/
│   ├── web/
│   │   ├── frontend/
│   │   │   └── components/
│   │   │       └── SettingsPanel.tsx
│   │   └── static/
│   └── widget/
│       └── launcher.py
├── mcp/
│   ├── server.py
│   └── tools.py
├── evaluation/
│   ├── datasets/
│   ├── queries.yaml
│   ├── accuracy.py
│   └── benchmarks.py
├── scripts/
│   ├── preprocess.py
│   ├── reindex.py
│   └── dev_bootstrap.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── corpus/
    │   └── expected/
    ├── unit/
    │   ├── model_clients/
    │   ├── embeddings/
    │   ├── inference/
    │   ├── ingestion/
    │   ├── db/
    │   └── core/
    ├── integration/
    └── e2e/
```

### `config/`
Configuration management: settings loading, model definitions, and path configurations.

### `core/`
Application core: dependency injection context, bootstrap logic, wiring, and lifecycle management.

### `model_clients/`
Provider-agnostic model client abstractions: base interfaces, provider implementations (OpenAI, Google, Ollama), and a registry for client selection.

### `embeddings/`
Embedding facade layer: router for selecting embedding clients and high-level embedding API.

### `inference/`
Inference and retrieval layer: RAG orchestration, retrieval, citation formatting, and response generation.

### `backend/`
FastAPI backend: REST API routes for chat, files, jobs, and settings management.

### `ingestion/`
Document ingestion pipeline: extractors, chunking algorithms, and indexing orchestration.

### `db/`
Database layer: metadata storage, vector store, settings persistence, and schema definitions.

### `watcher/`
Filesystem monitoring: file watcher, event debouncing, and normalized event types.

### `jobs/`
Job processing: queue abstraction, scheduler, async workers, and job state management.

### `ui/`
User interfaces: web frontend components and widget launcher.

### `mcp/`
MCP server: Model Context Protocol server exposing retrieval and Q&A tools.

### `evaluation/`
Evaluation harness: accuracy testing, benchmarks, and evaluation datasets.

### `scripts/`
Utility scripts: preprocessing, reindexing, and developer bootstrap helpers.

### `tests/`
Test suite: unit tests, integration tests, end-to-end tests, and test fixtures.
