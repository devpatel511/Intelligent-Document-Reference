"""Chat / inference endpoints."""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_context
from core.context import AppContext
from core.runtime_config import build_runtime_client, resolve_runtime_preferences
from inference.responder import Responder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_API_AUTH_ERROR_HINTS = (
    "incorrect api key",
    "invalid api key",
    "api key not valid",
    "unauthorized",
    "authentication",
    "permission denied",
    "forbidden",
    "invalid x-api-key",
    "401",
    "403",
)


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None
    inference_backend: Optional[str] = None
    mode: Optional[str] = "retrieval"
    selected_files: Optional[List[str]] = None
    temperature: Optional[float] = 0.7
    context_size: Optional[int] = 4096
    top_k: Optional[int] = 5
    system_prompt: Optional[str] = None


@router.post("/reset")
async def reset_chat(ctx: AppContext = Depends(get_context)):
    """Clear server-side chat history. Call when the UI starts a new conversation."""
    if ctx.chat_history:
        ctx.chat_history.clear()
    return {"ok": True}


@router.get("/status")
async def status(ctx: AppContext = Depends(get_context)):
    """Health check: report whether the RAG pipeline is ready and how many files/chunks are indexed."""
    ready = bool(ctx.db and ctx.embedding_client and ctx.inference_client)
    indexed_files = 0
    indexed_chunks = 0
    outdated_files = 0
    if ctx.db:
        try:
            conn = ctx.db._get_conn()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM files WHERE status='indexed'"
                ).fetchone()
                indexed_files = row["cnt"] if row else 0
                row = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()
                indexed_chunks = row["cnt"] if row else 0
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM files WHERE status='outdated'"
                ).fetchone()
                outdated_files = row["cnt"] if row else 0
            finally:
                conn.close()
        except Exception:
            pass
    runtime_prefs = resolve_runtime_preferences(ctx)
    return {
        "ready": ready,
        "indexed_files": indexed_files,
        "indexed_chunks": indexed_chunks,
        "outdated_files": outdated_files,
        "reindex_required": outdated_files > 0,
        "embedding_backend": runtime_prefs.get("embedding_backend"),
        "inference_backend": runtime_prefs.get("inference_backend"),
        "embedding_model": runtime_prefs.get("embedding_model"),
        "inference_model": runtime_prefs.get("inference_model"),
    }


@router.post("/query")
async def query(request: QueryRequest, ctx: AppContext = Depends(get_context)):
    """Process a chat query through the RAG pipeline.

    1. Check if session is dirty (files added/deleted); clear cache if needed.
    2. Embed the query using the configured embedding client.
    3. Retrieve the top-k most relevant chunks from the vector store.
    4. Include chat history context in the LLM prompt.
    5. Feed the chunks + query + history into the LLM to produce a cited answer.
    6. Log the turn to chat history.
    """
    if not ctx.db:
        raise HTTPException(status_code=503, detail="Database not initialised")
    if not ctx.embedding_client:
        raise HTTPException(status_code=503, detail="Embedding client not available")
    if not ctx.inference_client:
        raise HTTPException(status_code=503, detail="Inference client not available")

    # Check dirty flag and clear cache if files were added/deleted
    if ctx.dirty:
        if ctx.retrieval_cache:
            ctx.retrieval_cache.clear()
        ctx.dirty = False
        logger.info("Session marked as dirty; retrieval cache cleared")

    try:
        runtime_prefs = resolve_runtime_preferences(ctx)
        if request.inference_backend:
            runtime_prefs["inference_backend"] = request.inference_backend
        effective_backend = runtime_prefs.get("inference_backend")
        # Use a request-level model override so chat dropdown selections take
        # effect immediately without requiring a full settings save/restart.
        inference_client = build_runtime_client(
            ctx,
            kind="inference",
            prefs=runtime_prefs,
            model_override=request.model,
        )

        # Build chat history context for LLM
        chat_history_context = None
        if ctx.chat_history:
            chat_history_context = ctx.chat_history.get_context()

        responder = Responder(
            db=ctx.db,
            embedding_client=ctx.embedding_client,
            inference_client=inference_client,
            cache=ctx.retrieval_cache,
        )
        start_time = time.monotonic()
        result = await responder.respond(
            query=request.query,
            top_k=request.top_k or 5,
            selected_files=request.selected_files,
            model=request.model,
            temperature=request.temperature,
            context_size=request.context_size,
            system_prompt=request.system_prompt,
            inference_backend=effective_backend,
            chat_history_context=chat_history_context,
            runtime_prefs=runtime_prefs,
        )
        processing_time_ms = round((time.monotonic() - start_time) * 1000)

        # Log this turn to chat history for future queries
        if ctx.chat_history:
            ctx.chat_history.add_turn(
                user_query=request.query,
                assistant_response=result["answer"],
                metadata={
                    "model": request.model,
                    "inference_backend": effective_backend,
                    "top_k": request.top_k or 5,
                },
            )

    except Exception:
        logger.exception("RAG pipeline error")
        detail = "Error processing query. Make sure you have a valid backend model and/or API key set."
        status_code = 500
        msg = ""
        try:
            import traceback

            msg = traceback.format_exc().lower()
        except Exception:
            msg = ""

        if "dimension mismatch" in msg or "expected" in msg and "received" in msg:
            status_code = 409
            detail = (
                "Embedding/vector dimension mismatch detected. "
                "Re-save embedding settings to auto-align dimension and then reindex."
            )
        elif any(hint in msg for hint in _API_AUTH_ERROR_HINTS):
            status_code = 401
            detail = (
                "Model request failed. Either you were rate limited or your API key appears invalid/"
                "missing for the selected backend. Update it in Settings > Model Configuration and "
                "save settings, then try again."
            )
        raise HTTPException(status_code=status_code, detail=detail)

    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "model": request.model,
        "mode": request.mode,
        "processing_time_ms": processing_time_ms,
    }
