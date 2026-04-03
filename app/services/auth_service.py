"""Thin service functions for auth and user management."""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog

from app.exceptions import ConflictException, FintechBackendException
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.security import create_access_token, hash_password, verify_password


logger = structlog.get_logger(__name__)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a user by primary key."""

    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    """Fetch a non-deleted user by username."""

    return db.scalar(
        select(User).where(
            User.username == username,
            User.is_deleted.is_(False),
        )
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a non-deleted user by email."""

    return db.scalar(
        select(User).where(
            User.email == email,
            User.is_deleted.is_(False),
        )
    )


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a user with the simplest role bootstrap rule."""

    logger.info("user_create_started", username=user_data.username)
    first_user = db.scalar(select(User).where(User.is_deleted.is_(False)).limit(1))
    role = UserRole.ADMIN if first_user is None else UserRole.VIEWER

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=role,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        logger.exception("user_create_failed", username=user_data.username, error=str(exc))
        raise FintechBackendException("Unable to create user", sys) from exc

    logger.info("user_create_succeeded", user_id=user.id, role=user.role.value)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate login credentials and return the user when valid."""

    logger.info("user_authentication_started", username=username)
    user = get_user_by_username(db, username)
    if user is None:
        logger.warning("user_authentication_failed_not_found", username=username)
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning("user_authentication_failed_invalid_password", username=username)
        return None

    logger.info("user_authentication_succeeded", user_id=user.id)
    return user


def create_user_token(user: User) -> str:
    """Create a JWT token for a user."""

    return create_access_token(user.id)


def list_users(db: Session) -> list[User]:
    """Return all non-deleted users."""

    logger.info("users_fetch_started")
    users = db.scalars(
        select(User).where(User.is_deleted.is_(False)).order_by(User.id)
    ).all()
    user_list = list(users)
    logger.info("users_fetch_succeeded", user_count=len(user_list))
    return user_list


def update_user_status(db: Session, user: User, is_active: bool) -> User:
    """Update the active state for a user."""

    logger.info("user_status_update_started", user_id=user.id, is_active=is_active)
    user.is_active = is_active

    try:
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        logger.exception("user_status_update_failed", user_id=user.id, error=str(exc))
        raise FintechBackendException("Unable to update user status", sys) from exc

    logger.info("user_status_update_succeeded", user_id=user.id, is_active=user.is_active)
    return user


def update_user_details(db: Session, user: User, user_data: UserUpdate) -> User:
    """Update allowed user fields for an existing user."""

    logger.info("user_details_update_started", user_id=user.id)
    updates = user_data.model_dump(exclude_unset=True)

    if "username" in updates and updates["username"] != user.username:
        existing_user = get_user_by_username(db, updates["username"])
        if existing_user is not None and existing_user.id != user.id:
            logger.warning("user_details_update_conflict", field="username", user_id=user.id)
            raise ConflictException("Username already exists", sys)

    if "email" in updates and updates["email"] != user.email:
        existing_user = get_user_by_email(db, updates["email"])
        if existing_user is not None and existing_user.id != user.id:
            logger.warning("user_details_update_conflict", field="email", user_id=user.id)
            raise ConflictException("Email already exists", sys)

    for field_name, field_value in updates.items():
        setattr(user, field_name, field_value)

    try:
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        logger.exception("user_details_update_failed", user_id=user.id, error=str(exc))
        raise FintechBackendException("Unable to update user details", sys) from exc

    logger.info("user_details_update_succeeded", user_id=user.id)
    return user


def soft_delete_user(db: Session, user: User) -> User:
    """Soft delete a user and deactivate the account."""

    logger.info("user_soft_delete_started", user_id=user.id)
    user.is_deleted = True
    user.is_active = False

    try:
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        logger.exception("user_soft_delete_failed", user_id=user.id, error=str(exc))
        raise FintechBackendException("Unable to delete user", sys) from exc

    logger.info("user_soft_delete_succeeded", user_id=user.id)
    return user
