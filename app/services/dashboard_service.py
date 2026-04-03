"""Thin service functions for dashboard features."""

from collections import defaultdict
from decimal import Decimal
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog

from app.exceptions import FintechBackendException
from app.models.transaction import FinancialRecord, RecordType
from app.schemas.dashboard import (
    CategoryTotalOut,
    DashboardSummaryOut,
    DashboardTrendOut,
    RecentActivityOut,
)


logger = structlog.get_logger(__name__)
ZERO_DECIMAL = Decimal("0.00")


def get_dashboard_records(db: Session) -> list[FinancialRecord]:
    """Return all non-deleted records ordered for dashboard use."""

    logger.info("dashboard_records_fetch_started")
    try:
        records = db.scalars(
            select(FinancialRecord)
            .where(FinancialRecord.is_deleted.is_(False))
            .order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
        ).all()
    except Exception as exc:
        logger.exception("dashboard_records_fetch_failed", error=str(exc))
        raise FintechBackendException("Unable to load dashboard data", sys) from exc

    record_list = list(records)
    logger.info("dashboard_records_fetch_succeeded", record_count=len(record_list))
    return record_list


def build_dashboard_summary(records: list[FinancialRecord]) -> DashboardSummaryOut:
    """Build dashboard totals, category totals, and recent activity."""

    logger.info("dashboard_summary_build_started", record_count=len(records))
    total_income = ZERO_DECIMAL
    total_expenses = ZERO_DECIMAL
    category_totals: dict[str, Decimal] = defaultdict(lambda: ZERO_DECIMAL)

    for record in records:
        amount = Decimal(record.amount)
        if record.record_type == RecordType.INCOME:
            total_income += amount
        else:
            total_expenses += amount
        category_totals[record.category] += amount

    category_total_items = [
        CategoryTotalOut(category=category, total=total)
        for category, total in sorted(
            category_totals.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    recent_activity = [
        RecentActivityOut(
            id=record.id,
            amount=Decimal(record.amount),
            record_type=record.record_type,
            category=record.category,
            record_date=record.record_date,
            description=record.description,
        )
        for record in records[:5]
    ]
    summary = DashboardSummaryOut(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=total_income - total_expenses,
        category_totals=category_total_items,
        recent_activity=recent_activity,
    )
    logger.info(
        "dashboard_summary_build_succeeded",
        total_income=str(summary.total_income),
        total_expenses=str(summary.total_expenses),
        recent_activity_count=len(summary.recent_activity),
    )
    return summary


def build_dashboard_trends(records: list[FinancialRecord]) -> list[DashboardTrendOut]:
    """Build monthly trend points from non-deleted records."""

    logger.info("dashboard_trends_build_started", record_count=len(records))
    grouped: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "income": ZERO_DECIMAL,
            "expenses": ZERO_DECIMAL,
        }
    )

    for record in records:
        period = record.record_date.strftime("%Y-%m")
        amount = Decimal(record.amount)
        if record.record_type == RecordType.INCOME:
            grouped[period]["income"] += amount
        else:
            grouped[period]["expenses"] += amount

    trends = [
        DashboardTrendOut(
            period=period,
            income=values["income"],
            expenses=values["expenses"],
            net_balance=values["income"] - values["expenses"],
        )
        for period, values in sorted(grouped.items())
    ]
    logger.info("dashboard_trends_build_succeeded", trend_count=len(trends))
    return trends
