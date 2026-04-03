"""Pydantic schemas for user and auth endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


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


class UserUpdate(BaseModel):
    """Payload for updating user details."""

    username: str | None = None
    email: str | None = None
    role: UserRole | None = None


class UserOut(UserBase):
    """User response model."""

    id: int
    role: UserRole
    is_active: bool
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
