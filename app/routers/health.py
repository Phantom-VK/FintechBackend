"""Health and root routes."""

from fastapi import APIRouter, Depends
import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)


@router.get("/")
async def read_root():
    """Return a simple root response."""

    logger.info("root_route_called")
    return {"message": "Finance backend is running"}


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check API and database availability."""

    db.execute(text("SELECT 1"))
    logger.info("health_check_called")
    return {"status": "ok"}
