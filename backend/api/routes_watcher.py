"""Watcher endpoints (manage watched paths)."""

import os

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_context
from backend.schemas import WatchPathRequest, WatchPathResponse
from core.context import AppContext
from watcher import FileRegistry

router = APIRouter(prefix="/watcher", tags=["watcher"])


def _get_registry(ctx: AppContext = Depends(get_context)) -> FileRegistry:
    if ctx.watcher is None:
        raise HTTPException(status_code=503, detail="Watcher not initialized")
    return ctx.watcher.db


@router.post("/path", response_model=WatchPathResponse)
async def add_watch_path(
    req: WatchPathRequest,
    registry: FileRegistry = Depends(_get_registry),
):
    clean_path = os.path.abspath(os.path.expanduser(req.path))

    if not os.path.exists(clean_path):
        raise HTTPException(
            status_code=400, detail=f"Path does not exist: {clean_path}"
        )

    clean_excluded = []
    if req.excluded_files:
        clean_excluded = [
            os.path.abspath(os.path.expanduser(f)) for f in req.excluded_files
        ]

    registry.add_watch_path(clean_path, clean_excluded)
    updated_paths = registry.get_watch_paths()
    return {"status": "added", "active_paths": updated_paths}


@router.get("/path")
async def get_watch_paths(
    registry: FileRegistry = Depends(_get_registry),
):
    return {"active_paths": registry.get_watch_paths()}


@router.delete("/path", response_model=WatchPathResponse)
async def remove_watch_path_by_path(
    req: WatchPathRequest,
    registry: FileRegistry = Depends(_get_registry),
):
    clean_path = os.path.abspath(os.path.expanduser(req.path))
    registry.remove_watch_path(clean_path)
    return {"status": "removed", "active_paths": registry.get_watch_paths()}
