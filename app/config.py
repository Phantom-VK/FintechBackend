"""Application configuration values."""

APP_TITLE = "Finance Data Processing and Access Control Backend"
APP_VERSION = "0.1.0"

DATABASE_URL = "sqlite:///./finance.db"
SECRET_KEY = "finance-backend-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
