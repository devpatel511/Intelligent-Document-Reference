"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import List, Optional

class WatchPathRequest(BaseModel):
    path: str
    excluded_files: Optional[List[str]] = []

class WatchPathResponse(BaseModel):
    status: str
    active_paths: List[dict]


