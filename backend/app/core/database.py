"""SQLAlchemy engine/session setup and migration bootstrap.

The default database is a local SQLite file.  The persistence layer is written
against SQLAlchemy's dialect-neutral API so PostgreSQL can be introduced later
by changing ``CAREERPILOT_DATABASE_URL`` without rewriting services.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.models import base  # noqa: F401  (registers declarative base)

logger = logging.getLogger("careerpilot.database")

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _configure_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    if hasattr(dbapi_connection, "execute"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _configure_sqlite_wal(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def create_engine_for_url(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            pool_pre_ping=True,
        )
    return create_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)


def init_engine(settings=None) -> tuple[Engine, sessionmaker]:
    """Create (or recreate) the global engine and session factory."""
    global engine, SessionLocal
    settings = settings or get_settings()
    url = settings.resolved_database_url
    if url.startswith("sqlite"):
        db_path = Path(url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine_for_url(url)

    if url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_foreign_keys)
        event.listen(engine, "connect", _configure_sqlite_wal)

    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    return engine, SessionLocal


def get_engine() -> Engine:
    if engine is None:
        init_engine()
    assert engine is not None
    return engine


def get_session_factory() -> sessionmaker:
    if SessionLocal is None:
        init_engine()
    assert SessionLocal is not None
    return SessionLocal


def run_migrations() -> None:
    """Apply Alembic migrations to ``head``.  Idempotent; safe at startup."""
    from app import models  # noqa: F401  (ensure all models registered)

    alembic_cfg_path = os.environ.get("CAREERPILOT_ALEMBIC_CONFIG")
    if alembic_cfg_path:
        cfg = Config(alembic_cfg_path)
    else:
        cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    script_location = str(Path(__file__).resolve().parents[2] / "migrations")
    cfg.set_main_option("script_location", script_location)

    settings = get_settings()
    # Alembic reads the URL from env; pass the resolved URL explicitly.
    cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url)
    cfg.attributes.setdefault("configure_logger", False)
    command.upgrade(cfg, "head")


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
