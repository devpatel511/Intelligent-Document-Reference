"""File metadata endpoints."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

try:
    from watcher.core.database import FileRegistry
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from watcher.core.database import FileRegistry

router = APIRouter(prefix="/files", tags=["files"])

# Path to file indexing config; project root is parent of config dir
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "file_indexing.yaml"
PROJECT_ROOT = CONFIG_PATH.parent.parent


def _to_full_path(path: str, base: Path = PROJECT_ROOT) -> str:
    """Convert a path to absolute; use project root if path is relative."""
    p = (path or "").strip()
    if not p:
        return p
    path_obj = Path(p)
    if path_obj.is_absolute():
        return str(path_obj.resolve())
    return str((base / p).resolve())


def _paths_to_full_paths(paths: list, base: Path = PROJECT_ROOT) -> list:
    return [_to_full_path(x, base) for x in (paths or [])]


def _sync_watcher_to_inclusion_directories(directories: List[str]) -> None:
    """Sync monitor_config so only these directories are active (same logic as POST /watcher/sync)."""
    db_path = PROJECT_ROOT / "file_registry.db"
    if not db_path.exists():
        return
    registry = FileRegistry(db_path=str(db_path))
    raw = [p.strip() for p in (directories or []) if p and p.strip()]
    inclusion_set = {os.path.abspath(os.path.expanduser(p)).rstrip(os.sep) for p in raw}
    all_db_paths = registry.get_all_monitor_paths()
    for db_path in all_db_paths:
        normalized_db = db_path.rstrip(os.sep)
        if normalized_db not in inclusion_set:
            registry.remove_watch_path(db_path)
    for p in raw:
        full_path = os.path.abspath(os.path.expanduser(p))
        registry.add_watch_path(full_path, [])


def load_file_indexing_config() -> Dict[str, Any]:
    """Load file indexing configuration from YAML."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading file indexing config: {e}")
    return {
        "inclusion": {"files": [], "directories": []},
        "exclusion": {"files": [], "directories": [], "patterns": []},
        "context": {"files": []},
    }


def save_file_indexing_config(config: Dict[str, Any]) -> None:
    """Save file indexing configuration to YAML."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


class FileIndexingUpdate(BaseModel):
    inclusion: Optional[Dict[str, List[str]]] = None
    exclusion: Optional[Dict[str, List[str]]] = None
    context: Optional[Dict[str, List[str]]] = None


def build_file_tree(path: str, base_path: str = "") -> Dict[str, Any]:
    """Recursively build file tree structure."""
    full_path = Path(path)
    if not full_path.exists():
        return []

    nodes = []
    try:
        for item in sorted(full_path.iterdir()):
            if item.name.startswith("."):
                continue

            relative_path = str(
                item.relative_to(Path(base_path) if base_path else Path.cwd())
            )
            node = {
                "id": relative_path.replace(os.sep, "_"),
                "name": item.name,
                "type": "folder" if item.is_dir() else "file",
                "path": (
                    f"/{relative_path}"
                    if not relative_path.startswith("/")
                    else relative_path
                ),
            }

            if item.is_dir():
                children = build_file_tree(str(item), base_path or str(full_path))
                if children:
                    node["children"] = children

            nodes.append(node)
    except PermissionError:
        pass

    return nodes


@router.get("/")
async def list_files():
    """List available files in a tree structure."""
    # Return empty file tree by default - user must import folders
    # This prevents auto-importing the project folder
    return {"files": []}


@router.get("/indexing")
async def get_file_indexing_config():
    """Get current file indexing configuration."""
    return load_file_indexing_config()


@router.post("/indexing")
async def update_file_indexing_config(update: FileIndexingUpdate):
    """Update file indexing configuration."""
    config = load_file_indexing_config()

    if update.inclusion is not None:
        inclusion_data = {
            "files": _paths_to_full_paths(update.inclusion.get("files", [])),
            "directories": _paths_to_full_paths(
                update.inclusion.get("directories", [])
            ),
        }
        config["inclusion"] = inclusion_data

    if update.exclusion is not None:
        exclusion_data = {
            "files": _paths_to_full_paths(update.exclusion.get("files", [])),
            "directories": _paths_to_full_paths(
                update.exclusion.get("directories", [])
            ),
            "patterns": update.exclusion.get("patterns", []),
        }
        config["exclusion"] = exclusion_data

    if update.context is not None:
        context_files = update.context.get("files", [])
        filtered_files = [f for f in context_files if not f.endswith("/")]
        config["context"] = {"files": _paths_to_full_paths(filtered_files)}

    save_file_indexing_config(config)
    # Sync monitor_config with the inclusion list we just saved (so is_active matches YAML)
    _sync_watcher_to_inclusion_directories(
        config.get("inclusion", {}).get("directories", [])
    )
    return {"status": "ok", "config": config}


@router.get("/context")
async def get_context_files():
    """Get files selected for context (only leaf files, not directories)."""
    config = load_file_indexing_config()
    context_files = config.get("context", {}).get("files", [])
    # Filter out directories - only return actual files
    # Directories typically end with '/' or have no file extension
    # For now, we'll filter anything ending with '/'
    filtered = []
    for f in context_files:
        if not f.endswith("/"):
            # Also check if it's a real file path (has extension or is a known file)
            path_obj = Path(f)
            if path_obj.suffix or not path_obj.exists() or path_obj.is_file():
                filtered.append(f)
    return {"files": filtered}
