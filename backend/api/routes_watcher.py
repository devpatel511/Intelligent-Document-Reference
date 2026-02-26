"""Watcher endpoints (manage watched paths)."""

import os
import sys

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import SyncPathsRequest, WatchPathRequest, WatchPathResponse

# Assuming the app is run from root, we can import watcher
try:
    from watcher.core.database import FileRegistry
except ImportError:
    # Fallback for when running backend isolation without watcher pkg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from watcher.core.database import FileRegistry
router = APIRouter(prefix="/watcher", tags=["watcher"])

# Initialize DB connection (lightweight)
# Ensure we point to the same DB file as the watcher
# We assume the DB is at root "file_registry.db"
DB_PATH = os.path.abspath("file_registry.db")
registry = FileRegistry(db_path=DB_PATH)


@router.post("/path", response_model=WatchPathResponse)
async def add_watch_path(req: WatchPathRequest):
    # Normalize the main path
    clean_path = os.path.abspath(os.path.expanduser(req.path))

    if not os.path.exists(clean_path):
        raise HTTPException(
            status_code=400, detail=f"Path does not exist: {clean_path}"
        )

    # Normalize excluded files
    clean_excluded = []
    if req.excluded_files:
        clean_excluded = [
            os.path.abspath(os.path.expanduser(f)) for f in req.excluded_files
        ]

    registry.add_watch_path(clean_path, clean_excluded)
    updated_paths = registry.get_watch_paths()
    return {"status": "added", "active_paths": updated_paths}


@router.get("/path")
async def get_watch_paths():
    return {"active_paths": registry.get_watch_paths()}


@router.delete("/path", response_model=WatchPathResponse)
async def remove_watch_path_by_path(
    path: str = Query(..., description="Path to stop watching")
):
    """Remove a path from the watcher (sets is_active=0). Uses query param so DELETE works reliably."""
    clean_path = os.path.abspath(os.path.expanduser(path))
    registry.remove_watch_path(clean_path)
    return {"status": "removed", "active_paths": registry.get_watch_paths()}


@router.post("/sync", response_model=WatchPathResponse)
async def sync_watch_paths(req: SyncPathsRequest):
    """
    Sync monitor_config with the inclusion list from the UI (YAML stores full paths).
    - Any path in monitor_config that is NOT in req.paths (normalized) gets is_active=0.
    - Any path in req.paths gets added/updated with is_active=1.
    All paths are normalized (abspath, no trailing sep) for comparison.
    """
    raw = [p.strip() for p in (req.paths or []) if p and p.strip()]
    inclusion_set = {os.path.abspath(os.path.expanduser(p)).rstrip(os.sep) for p in raw}
    all_db_paths = registry.get_all_monitor_paths()
    for db_path in all_db_paths:
        normalized_db = db_path.rstrip(os.sep)
        if normalized_db not in inclusion_set:
            registry.remove_watch_path(db_path)
    for p in raw:
        full_path = os.path.abspath(os.path.expanduser(p))
        registry.add_watch_path(full_path, [])
    return {"status": "synced", "active_paths": registry.get_watch_paths()}
