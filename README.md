# Intelligent Document Reference

Local-first RAG app for document ingestion and citation-grounded Q&A.

- Backend: FastAPI
- Frontend: React/Vite
- Storage: SQLite + sqlite-vec

## Quick Start (Production)

**Prerequisites:** `uv` — [github.com/astral-sh/uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

Run command:

```bash
uv run app.py
```

Default app URL: http://127.0.0.1:8000

## Configuration (UI First)

Use the Settings UI in the app to configure:
1. Embedding model
2. Inference model
3. API keys

![Model Configuration Page](assets/model_configuration.png)

Optionally, you may use an environment file to do this [.env.example](.env.example).

---

## Development

**Prerequisites:** Node.js 22+ — [nodejs.org](https://nodejs.org/)

Run commands:

```bash
uv run app.py --setup
uv run app.py --dev
```

Optionally, run Electron mini-mode helper (**experimental**):

```bash
uv run app.py --dev --electron
```

For all available flags:

```bash
uv run app.py --help
```

## Contributing

```bash
uv sync --group dev					# install test deps
uv run scripts/cspyformatter.py  	# run formatting
uv run pytest						# run all tests
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Port already in use | `uv run app.py --port 8080` |
| Frontend not loading in production | `uv run app.py --setup` |
| Reset local DB/indexing state | `uv run app.py --reset` |
| Folder picker unavailable | See [docs/TKINTER_SETUP.md](docs/TKINTER_SETUP.md) |
