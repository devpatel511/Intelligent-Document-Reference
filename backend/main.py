"""FastAPI app entrypoint (stub)."""
from fastapi import FastAPI
from backend.api import routes_chat, routes_files, routes_jobs, routes_settings

app = FastAPI(title="local-rag-backend")
app.include_router(routes_chat.router)
app.include_router(routes_files.router)
app.include_router(routes_jobs.router)
app.include_router(routes_settings.router)

