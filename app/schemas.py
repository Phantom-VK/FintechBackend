"""Pydantic schemas for API requests and responses."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import RecordType, UserRole


class UserBase(BaseModel):
    """Shared user fields."""

    username: str
    email: str


class UserCreate(UserBase):
    """Payload for creating a user account."""

    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    """Payload for logging in with username and password."""

    username: str
    password: str


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class UserStatusUpdate(BaseModel):
    """Payload for toggling a user's active state."""

    is_active: bool


class UserOut(UserBase):
    """User response model."""

    id: int
    role: UserRole
    is_active: bool
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
