import importlib

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import models
from app.database.database import get_db


@pytest.fixture(scope="session")
def app(request):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("API_KEY_HASH_PEPPER", "test-pepper")
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "1")

    import app.core.config as config
    import app.core.security as security
    import app.main as main

    importlib.reload(config)
    importlib.reload(security)
    importlib.reload(main)

    if not any(route.path == "/_test" for route in main.app.router.routes):
        main.app.add_api_route("/_test", lambda: {"ok": True}, methods=["GET"])

    if not any(route.path == "/_auth_test" for route in main.app.router.routes):
        main.app.add_api_route(
            "/_auth_test",
            lambda: {"ok": True},
            methods=["GET"],
            dependencies=[Depends(security.require_api_key)],
        )

    def cleanup():
        monkeypatch.undo()

    request.addfinalizer(cleanup)
    return main.app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(
        bind=engine,
        tables=[models.User.__table__, models.APIKey.__table__],
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(app, db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
