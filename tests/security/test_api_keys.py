from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core import security
from app.database.models import APIKey, User


def test_hash_api_key_deterministic():
    first = security._hash_api_key("raw-key")
    second = security._hash_api_key("raw-key")
    assert first == second
    assert first != "raw-key"


def test_require_api_key_missing_raises(db_session, monkeypatch):
    monkeypatch.setattr(security, "DEBUG", False)
    monkeypatch.setattr(security, "API_KEY", None)

    with pytest.raises(HTTPException) as exc:
        security.require_api_key(api_key=None, db=db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing API key"


def test_require_api_key_invalid_raises(db_session, monkeypatch):
    monkeypatch.setattr(security, "DEBUG", False)
    monkeypatch.setattr(security, "API_KEY", None)

    with pytest.raises(HTTPException) as exc:
        security.require_api_key(api_key="bad-key", db=db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid API key"


def test_require_api_key_allows_env_key(db_session, monkeypatch):
    monkeypatch.setattr(security, "DEBUG", False)
    monkeypatch.setattr(security, "API_KEY", "env-key")

    assert security.require_api_key(api_key="env-key", db=db_session) is None


def test_require_api_key_db_key_updates_last_used(db_session, monkeypatch):
    monkeypatch.setattr(security, "DEBUG", False)
    monkeypatch.setattr(security, "API_KEY", None)

    user = User(email="user@example.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    raw_key = "db-key"
    key_hash = security._hash_api_key(raw_key)
    api_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db_session.add(api_key)
    db_session.commit()

    assert api_key.last_used_at is None
    assert security.require_api_key(api_key=raw_key, db=db_session) is None

    db_session.refresh(api_key)
    assert api_key.last_used_at is not None


def test_auth_route_allows_valid_env_key(client):
    response = client.get("/_auth_test", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_auth_route_rejects_missing_key(client):
    response = client.get("/_auth_test")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"
