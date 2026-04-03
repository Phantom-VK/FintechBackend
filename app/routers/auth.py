"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_user_token,
    get_user_by_email,
    get_user_by_username,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Register a new user."""

    existing_username = get_user_by_username(db, user_data.username)
    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = get_user_by_email(db, user_data.email)
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    return create_user(db, user_data)


@router.post("/login", response_model=Token)
def login_user(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Log in a user and return a bearer token."""

    user = authenticate_user(db, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot log in",
        )

    return Token(access_token=create_user_token(user))


@router.get("/me", response_model=UserOut)
def get_logged_in_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the current authenticated user."""

    return current_user
