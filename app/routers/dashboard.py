"""Dashboard routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
import structlog
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardSummaryOut, DashboardTrendOut
from app.services.dashboard_service import (
    build_dashboard_summary,
    build_dashboard_trends,
    get_dashboard_records,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = structlog.get_logger(__name__)


@router.get("/summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
) -> DashboardSummaryOut:
    """Return dashboard totals, category totals, and recent activity."""

    logger.info(
        "dashboard_summary_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
    )
    records = get_dashboard_records(db)
    summary = build_dashboard_summary(records)
    logger.info(
        "dashboard_summary_completed",
        actor_user_id=current_user.id,
        recent_activity_count=len(summary.recent_activity),
    )
    return summary


@router.get("/trends", response_model=list[DashboardTrendOut])
async def get_dashboard_trends(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
) -> list[DashboardTrendOut]:
    """Return monthly dashboard trends."""

    logger.info(
        "dashboard_trends_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
    )
    records = get_dashboard_records(db)
    trends = build_dashboard_trends(records)
    logger.info(
        "dashboard_trends_completed",
        actor_user_id=current_user.id,
        trend_count=len(trends),
    )
    return trends
