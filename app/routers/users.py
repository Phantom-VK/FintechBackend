"""User management routes."""

import sys
from typing import Annotated

from fastapi import APIRouter, Depends
import structlog
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.exceptions import BadRequestException, ResourceNotFoundException
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserStatusUpdate
from app.services.auth_service import (
    get_user_by_id,
    list_users as list_all_users,
    update_user_status as update_user_status_service,
)


router = APIRouter(prefix="/users", tags=["users"])
logger = structlog.get_logger(__name__)


@router.get("/", response_model=list[UserOut])
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> list[User]:
    """Return all non-deleted users."""

    users = list_all_users(db)
    logger.info(
        "users_listed",
        actor_user_id=current_user.id,
        user_count=len(users),
    )
    return users


@router.patch("/{user_id}/status", response_model=UserOut)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> User:
    """Activate or deactivate a user."""

    user = get_user_by_id(db, user_id)
    if user is None or user.is_deleted:
        logger.warning("user_status_update_failed_not_found", actor_user_id=current_user.id)
        raise ResourceNotFoundException("User not found", sys)

    if user.id == current_user.id and not status_data.is_active:
        logger.warning("self_deactivation_blocked", actor_user_id=current_user.id)
        raise BadRequestException("You cannot deactivate your own account", sys)

    updated_user = update_user_status_service(db, user, status_data.is_active)
    logger.info(
        "user_status_updated",
        actor_user_id=current_user.id,
        target_user_id=updated_user.id,
        is_active=updated_user.is_active,
    )
    return updated_user
