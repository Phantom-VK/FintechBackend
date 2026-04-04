"""Shared helpers for backend tests."""

# pylint: disable=duplicate-code

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_test_engine(temp_dir_path: str, database_name: str):
    """Create a SQLite engine and session factory for test isolation."""

    db_path = Path(temp_dir_path) / database_name
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    return engine, session_local


def build_async_db_override(session_local):
    """Return an async dependency override that yields DB sessions."""

    async def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    return override_get_db
