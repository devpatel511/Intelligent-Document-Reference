"""Settings endpoints (get/update model backend selection)."""
from fastapi import APIRouter
router = APIRouter(prefix="/settings", tags=["settings"])

SETTINGS = {
    "embedding_backend": "api",
    "inference_backend": "api"
}

@router.get("/")
async def get_settings():
    return SETTINGS

@router.post("/update")
async def update_settings(payload: dict):
    SETTINGS.update(payload)
    return {"status": "ok", "settings": SETTINGS}

