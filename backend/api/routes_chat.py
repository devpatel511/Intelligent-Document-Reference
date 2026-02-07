"""Chat / inference endpoints."""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "gpt-4"
    mode: Optional[str] = "retrieval"
    selected_files: Optional[List[str]] = []
    temperature: Optional[float] = 0.7
    context_size: Optional[int] = 4096


@router.post("/query")
async def query(request: QueryRequest):
    """
    Process a chat query.

    TODO: Integrate with actual RAG pipeline and model clients.
    """
    # This is a stub implementation
    # In production, this should:
    # 1. Use the inference router to get the appropriate client
    # 2. Process the query through the RAG pipeline
    # 3. Return the answer with citations

    answer = f"This is a placeholder response. Your query was: '{request.query}'. "
    answer += f"Model: {request.model}, Mode: {request.mode}. "
    answer += "The actual RAG pipeline integration is pending."

    return {
        "answer": answer,
        "citations": [],
        "model": request.model,
        "mode": request.mode,
    }
