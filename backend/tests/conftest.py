"""Shared test fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def data_dir(tmp_path):
    path = tmp_path / "careerpilot-data"
    path.mkdir()
    os.environ["CAREERPILOT_DATA_DIR"] = str(path)
    os.environ["CAREERPILOT_DATABASE_URL"] = f"sqlite:///{path}/test.db"
    os.environ["CAREERPILOT_SCHEDULER_ENABLED"] = "false"
    # reset caches that captured earlier settings
    import app.core.config as config_module

    config_module.get_settings.cache_clear()
    import app.core.database as database_module

    database_module.engine = None
    database_module.SessionLocal = None
    yield path
    os.environ.pop("CAREERPILOT_DATA_DIR", None)
    os.environ.pop("CAREERPILOT_DATABASE_URL", None)
    config_module.get_settings.cache_clear()
    database_module.engine = None
    database_module.SessionLocal = None


@pytest.fixture()
def client(data_dir):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    from app.core.security import get_or_create_api_token

    token = get_or_create_api_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _seed_profile(client, auth_headers):
    """Ensure a profile (id=1) exists for tests that seed rows directly."""
    from app.core.database import get_session_factory
    from app.services.profile_service import get_or_create_profile

    from app.core.database import get_engine

    get_engine().connect().close()
    session = get_session_factory()()
    try:
        get_or_create_profile(session)
    finally:
        session.close()
    yield
