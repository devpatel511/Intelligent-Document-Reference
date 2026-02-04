# Local-first Intelligent Document Reference — Architecture Scaffold

This repository is an architecture-only scaffold for a local-first RAG system.

It contains packages, stub modules, and TODO markers for implementation tasks.

Use this scaffold as the starting point for development, tests, and documentation.

## Purpose

- Provide a clear, testable, provider-agnostic architecture.

- Make model switching first-class (local `ollama` vs API providers).

- Keep wiring and lifecycle separate (`core/`).

- Mirror the test structure to the application structure.

## How to use

1. Create a virtualenv and install dev deps (see `pyproject.toml`).

2. Implement modules incrementally; follow TODOs in stubs.

3. Use `core/bootstrap.py` to wire subsystems into `core/context.py`.

4. Run tests under `tests/` as they are implemented.

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

## Package Descriptions

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
