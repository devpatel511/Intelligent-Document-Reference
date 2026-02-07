"""File metadata endpoints."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/files", tags=["files"])

# Path to file indexing config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "file_indexing.yaml"


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
        # Ensure we have the right structure
        inclusion_data = {
            "files": update.inclusion.get("files", []),
            "directories": update.inclusion.get("directories", []),
        }
        config["inclusion"] = inclusion_data

    if update.exclusion is not None:
        # Ensure we have the right structure
        exclusion_data = {
            "files": update.exclusion.get("files", []),
            "directories": update.exclusion.get("directories", []),
            "patterns": update.exclusion.get("patterns", []),
        }
        config["exclusion"] = exclusion_data

    if update.context is not None:
        # Filter out directories, only keep files
        context_files = update.context.get("files", [])
        # Filter to only include actual files (not directories)
        filtered_files = [f for f in context_files if not f.endswith("/")]
        config["context"] = {"files": filtered_files}

    save_file_indexing_config(config)
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
