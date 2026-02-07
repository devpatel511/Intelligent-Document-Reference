"""Job control endpoints (stubs)."""

from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/enqueue")
async def enqueue(job: dict):
    return {"status": "enqueued"}
