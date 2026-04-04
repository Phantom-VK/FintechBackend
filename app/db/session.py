"""Database setup and session helpers."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Provide a database session for request handlers."""

    db = session_local()
    try:
        yield db
    finally:
        db.close()
