"""Pydantic schemas for financial record endpoints."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import RecordType


class SortOrder(str, Enum):
    """Supported sort directions for listing records."""

    ASC = "asc"
    DESC = "desc"


class TransactionSortField(str, Enum):
    """Supported sort fields for transaction listing."""

    RECORD_DATE = "record_date"
    AMOUNT = "amount"
    CREATED_AT = "created_at"


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


class FinancialRecordFilters:
    """Simple filter container for listing records."""

    def __init__(
        self,
        record_type: RecordType | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> None:
        self.record_type = record_type
        self.category = category
        self.date_from = date_from
        self.date_to = date_to


class FinancialRecordListOptions:
    """Pagination and sorting options for listing records."""

    def __init__(
        self,
        page: int = 1,
        limit: int = 10,
        sort_by: TransactionSortField = TransactionSortField.RECORD_DATE,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> None:
        self.page = page
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order


def get_financial_record_filters(
    record_type: RecordType | None = None,
    category: str | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> FinancialRecordFilters:
    """Build filter values from request query parameters."""

    return FinancialRecordFilters(
        record_type=record_type,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )


def get_financial_record_list_options(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: TransactionSortField = Query(default=TransactionSortField.RECORD_DATE),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> FinancialRecordListOptions:
    """Build pagination and sorting values from request query parameters."""

    return FinancialRecordListOptions(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


class FinancialRecordOut(FinancialRecordBase):
    """Financial record response model."""

    id: int
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialRecordListOut(BaseModel):
    """Paginated transaction list response."""

    items: list[FinancialRecordOut]
    total: int
    page: int
    limit: int
