"""Data models for analytics-service."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ServiceRequest(BaseModel):
    id: str
    payload: dict
    timestamp: datetime = datetime.utcnow()

class ServiceResponse(BaseModel):
    id: str
    result: dict
    status: str = "success"
    processing_time_ms: Optional[float] = None
