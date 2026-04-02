from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.db import get_db
from app.deps import get_current_user
from app.models import User, UserRole
from app.schemas import Token, UserCreate, UserLogin, UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    existing_username = db.scalar(
        select(User).where(
            User.username == user_data.username,
            User.is_deleted.is_(False),
        )
    )
    if existing_username is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    existing_email = db.scalar(
        select(User).where(
            User.email == user_data.email,
            User.is_deleted.is_(False),
        )
    )
    if existing_email is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

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


@router.post("/login", response_model=Token)
def login_user(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = db.scalar(
        select(User).where(
            User.username == credentials.username,
            User.is_deleted.is_(False),
        )
    )
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot log in",
        )

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def get_logged_in_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
