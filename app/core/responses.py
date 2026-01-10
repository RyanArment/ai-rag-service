"""
Unified response schemas for API endpoints.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class LLMCompletionResponse(BaseModel):
    """Response for LLM completion requests."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    latency_ms: Optional[float] = None


class StreamingChunk(BaseModel):
    """Single chunk in a streaming response."""
    content: str
    done: bool = False
    model: Optional[str] = None
    provider: Optional[str] = None
