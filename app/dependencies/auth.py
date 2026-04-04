"""Reusable FastAPI dependencies for authentication and authorization."""

from collections.abc import Callable
import sys
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return the authenticated active user for the request."""

    if credentials is None:
        raise AuthenticationException(
            "Authentication credentials were not provided",
            sys,
        )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise AuthenticationException("Invalid authentication credentials", sys)

    user = get_user_by_id(db, user_id)
    if user is None or user.is_deleted:
        raise AuthenticationException("User not found", sys)

    if not user.is_active:
        raise AuthorizationException("Inactive users cannot access this resource", sys)

    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Create a dependency that allows only specific user roles."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise AuthorizationException(
                "You do not have permission to access this resource",
                sys,
            )
        return current_user

    return role_checker
