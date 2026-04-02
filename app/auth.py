"""Authentication helpers for password hashing and JWT tokens."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password before saving it."""

    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored hash."""

    return pwd_context.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Create a signed access token for a user."""

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Decode a token and return the user id when valid."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, TypeError, ValueError):
        return None
