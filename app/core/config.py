"""Application configuration values."""

import os


APP_TITLE = "Finance Data Processing and Access Control Backend"
APP_VERSION = "0.1.0"


def get_env_value(name: str, default: str) -> str:
    """Return an environment value or the provided default when blank."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def get_env_int(name: str, default: int) -> int:
    """Return an integer environment value or the provided default."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


DATABASE_URL = get_env_value("DATABASE_URL", "sqlite:///./finance.db")
SECRET_KEY = get_env_value("SECRET_KEY", "finance-backend-secret-key")
ALGORITHM = get_env_value("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
