"""
API key security utilities.
"""
import hmac
import hashlib
from datetime import datetime
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

from sqlalchemy.orm import Session

from app.core.config import API_KEY, DEBUG, API_KEY_HASH_PEPPER
from app.database.database import get_db
from app.database.models import APIKey as APIKeyModel

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_api_key(raw_key: str) -> str:
    payload = f"{API_KEY_HASH_PEPPER}{raw_key}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_db_key_valid(db: Session, raw_key: str) -> bool:
    key_hash = _hash_api_key(raw_key)
    now = datetime.utcnow()
    record = (
        db.query(APIKeyModel)
        .filter(APIKeyModel.key_hash == key_hash)
        .filter(APIKeyModel.is_active.is_(True))
        .first()
    )
    if not record:
        return False
    if record.expires_at and record.expires_at <= now:
        return False
    record.last_used_at = now
    db.commit()
    return True


def require_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db),
) -> None:
    """Require API key for protected endpoints."""
    if DEBUG and not API_KEY:
        return
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if API_KEY and hmac.compare_digest(api_key, API_KEY):
        return
    if _is_db_key_valid(db, api_key):
        return
    raise HTTPException(status_code=401, detail="Invalid API key")
