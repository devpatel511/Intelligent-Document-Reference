"""Watcher endpoints (manage watched paths)."""
from fastapi import APIRouter, HTTPException
from backend.schemas import WatchPathRequest, WatchPathResponse
# Assuming the app is run from root, we can import watcher
try:
    from watcher.core.database import FileRegistry
except ImportError:
    # Fallback for when running backend isolation without watcher pkg
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from watcher.core.database import FileRegistry

import os

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
        raise HTTPException(status_code=400, detail=f"Path does not exist: {clean_path}")

    # Normalize excluded files
    clean_excluded = []
    if req.excluded_files:
        clean_excluded = [os.path.abspath(os.path.expanduser(f)) for f in req.excluded_files]
    
    registry.add_watch_path(clean_path, clean_excluded)
    updated_paths = registry.get_watch_paths()
    return {"status": "added", "active_paths": updated_paths}

@router.get("/path")
async def get_watch_paths():
    return {"active_paths": registry.get_watch_paths()}

@router.delete("/path/{path_id}")
async def remove_watch_path(path_id: int):
    registry.remove_watch_path_by_id(path_id)
    return {"status": "removed", "active_paths": registry.get_watch_paths()}
