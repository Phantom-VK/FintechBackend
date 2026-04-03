"""Thin service functions for auth and user management."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.security import create_access_token, hash_password, verify_password


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

    first_user = db.scalar(select(User).where(User.is_deleted.is_(False)).limit(1))
    role = UserRole.ADMIN if first_user is None else UserRole.VIEWER

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate login credentials and return the user when valid."""

    user = get_user_by_username(db, username)
    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_user_token(user: User) -> str:
    """Create a JWT token for a user."""

    return create_access_token(user.id)


def list_users(db: Session) -> list[User]:
    """Return all non-deleted users."""

    users = db.scalars(
        select(User).where(User.is_deleted.is_(False)).order_by(User.id)
    ).all()
    return list(users)


def update_user_status(db: Session, user: User, is_active: bool) -> User:
    """Update the active state for a user."""

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
