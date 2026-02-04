"""Chat / inference endpoints (stubs)."""
from fastapi import APIRouter
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query")
async def query(payload: dict):
    return {"answer": "stub", "citations": []}

