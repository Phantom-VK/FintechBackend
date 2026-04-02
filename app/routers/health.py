"""Health and root routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/")
def read_root():
    """Return a simple root response."""

    return {"message": "Finance backend is running"}


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check API and database availability."""

    db.execute(text("SELECT 1"))
    return {"status": "ok"}
