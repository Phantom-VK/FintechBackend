"""User management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserStatusUpdate
from app.services.auth_service import (
    get_user_by_id,
    list_users as list_all_users,
    update_user_status as update_user_status_service,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> list[User]:
    """Return all non-deleted users."""

    return list_all_users(db)


@router.patch("/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> User:
    """Activate or deactivate a user."""

    user = get_user_by_id(db, user_id)
    if user is None or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    return update_user_status_service(db, user, status_data.is_active)
