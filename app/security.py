"""Authentication helpers for password hashing and JWT tokens."""

from datetime import datetime, timedelta, timezone
import sys

from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.exceptions import FintechBackendException


logger = structlog.get_logger(__name__)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password before saving it."""

    logger.info("password_hash_requested")
    try:
        hashed_password = pwd_context.hash(password)
        logger.info("password_hash_created")
        return hashed_password
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception(
            "password_hash_failed",
            error_type=type(exc).__name__,
        )
        raise FintechBackendException(
            "Unable to process password securely",
            sys,
        ) from exc


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored hash."""

    logger.info("password_verification_requested")
    try:
        is_valid = pwd_context.verify(password, hashed_password)
        logger.info("password_verification_completed", is_valid=is_valid)
        return is_valid
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception(
            "password_verification_failed",
            error_type=type(exc).__name__,
        )
        return False


def create_access_token(user_id: int) -> str:
    """Create a signed access token for a user."""

    logger.info("access_token_creation_requested", user_id=user_id)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("access_token_created", user_id=user_id)
    return token


def decode_access_token(token: str) -> int | None:
    """Decode a token and return the user id when valid."""

    try:
        logger.info("access_token_decode_requested")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("access_token_missing_subject")
            return None
        parsed_user_id = int(user_id)
        logger.info("access_token_decoded", user_id=parsed_user_id)
        return parsed_user_id
    except (JWTError, TypeError, ValueError) as exc:
        logger.warning(
            "access_token_decode_failed",
            error_type=type(exc).__name__,
        )
        return None
