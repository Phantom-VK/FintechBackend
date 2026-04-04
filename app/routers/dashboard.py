"""Dashboard routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
import structlog
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    CategoryTotalOut,
    DashboardSummaryOut,
    DashboardTotalsOut,
    DashboardTrendOut,
    RecentActivityOut,
    TrendGroupBy,
)
from app.services.dashboard_service import (
    build_category_totals,
    build_dashboard_totals,
    build_dashboard_summary,
    build_dashboard_trends,
    build_recent_activity,
    get_dashboard_records,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = structlog.get_logger(__name__)


@router.get("/totals", response_model=DashboardTotalsOut)
async def get_dashboard_totals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
) -> DashboardTotalsOut:
    """Return top-level income, expense, and net totals."""

    logger.info(
        "dashboard_totals_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
    )
    records = get_dashboard_records(db)
    totals = build_dashboard_totals(records)
    logger.info(
        "dashboard_totals_completed",
        actor_user_id=current_user.id,
        net_balance=str(totals.net_balance),
    )
    return totals


@router.get("/category-totals", response_model=list[CategoryTotalOut])
async def get_dashboard_category_totals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
) -> list[CategoryTotalOut]:
    """Return category-wise totals for dashboard widgets."""

    logger.info(
        "dashboard_category_totals_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
    )
    records = get_dashboard_records(db)
    category_totals = build_category_totals(records)
    logger.info(
        "dashboard_category_totals_completed",
        actor_user_id=current_user.id,
        category_count=len(category_totals),
    )
    return category_totals


@router.get("/recent-activity", response_model=list[RecentActivityOut])
async def get_recent_activity(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
    limit: int = Query(default=5, ge=1, le=50),
) -> list[RecentActivityOut]:
    """Return recent transaction activity for dashboard widgets."""

    logger.info(
        "dashboard_recent_activity_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
        limit=limit,
    )
    records = get_dashboard_records(db)
    recent_activity = build_recent_activity(records, limit=limit)
    logger.info(
        "dashboard_recent_activity_completed",
        actor_user_id=current_user.id,
        recent_activity_count=len(recent_activity),
    )
    return recent_activity


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
    group_by: TrendGroupBy = Query(default=TrendGroupBy.MONTHLY),
) -> list[DashboardTrendOut]:
    """Return monthly or weekly dashboard trends."""

    logger.info(
        "dashboard_trends_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
        group_by=group_by.value,
    )
    records = get_dashboard_records(db)
    trends = build_dashboard_trends(records, group_by=group_by)
    logger.info(
        "dashboard_trends_completed",
        actor_user_id=current_user.id,
        trend_count=len(trends),
        group_by=group_by.value,
    )
    return trends
