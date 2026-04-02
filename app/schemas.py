from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import RecordType, UserRole


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserOut(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialRecordBase(BaseModel):
    amount: Decimal = Field(gt=0)
    record_type: RecordType
    category: str
    record_date: date
    description: str | None = None


class FinancialRecordCreate(FinancialRecordBase):
    pass


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    record_type: RecordType | None = None
    category: str | None = None
    record_date: date | None = None
    description: str | None = None


class FinancialRecordOut(FinancialRecordBase):
    id: int
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
