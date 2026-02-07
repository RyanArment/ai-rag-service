"""
API key security utilities.
"""
import hmac
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import API_KEY, DEBUG

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str = Security(api_key_header)) -> None:
    """Require API key for protected endpoints."""
    if DEBUG and not API_KEY:
        return
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    if not api_key or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
