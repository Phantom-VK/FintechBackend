"""Pydantic schemas for dashboard endpoints."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.transaction import RecordType


class CategoryTotalOut(BaseModel):
    """Category total used in dashboard summary responses."""

    category: str
    total: Decimal


class RecentActivityOut(BaseModel):
    """Compact transaction view for dashboard recent activity."""

    id: int
    amount: Decimal
    record_type: RecordType
    category: str
    record_date: date
    description: str | None = None


class DashboardSummaryOut(BaseModel):
    """High-level dashboard totals and recent activity."""

    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    category_totals: list[CategoryTotalOut]
    recent_activity: list[RecentActivityOut]


class DashboardTrendOut(BaseModel):
    """Monthly trend point for the dashboard."""

    period: str
    income: Decimal
    expenses: Decimal
    net_balance: Decimal
