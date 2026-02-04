"""File metadata endpoints (stubs)."""
from fastapi import APIRouter
router = APIRouter(prefix="/files", tags=["files"])

@router.get("/")
async def list_files():
    return {"files": []}

