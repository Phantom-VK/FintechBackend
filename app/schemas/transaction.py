"""Pydantic schemas for financial record endpoints."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import RecordType


class FinancialRecordBase(BaseModel):
    """Shared financial record fields."""

    amount: Decimal = Field(gt=0)
    record_type: RecordType
    category: str
    record_date: date
    description: str | None = None


class FinancialRecordCreate(FinancialRecordBase):
    """Payload for creating a financial record."""


class FinancialRecordUpdate(BaseModel):
    """Payload for updating a financial record."""

    amount: Decimal | None = Field(default=None, gt=0)
    record_type: RecordType | None = None
    category: str | None = None
    record_date: date | None = None
    description: str | None = None


class FinancialRecordOut(FinancialRecordBase):
    """Financial record response model."""

    id: int
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
