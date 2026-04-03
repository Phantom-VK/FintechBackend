"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from app import models as model_registry
from app.config import APP_TITLE, APP_VERSION
from app.database import Base, engine
from app.exceptions import FintechBackendException
from app.logging_config import setup_logging
from app.middleware import logging_middleware
from app.routers.dashboard import router as dashboard_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.transactions import router as transactions_router
from app.routers.users import router as users_router
from app.routers.utils import router as utils_router

log_file_path = setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables when the app starts."""

    _ = model_registry
    Base.metadata.create_all(bind=engine)
    logger.info("application_started", log_file=log_file_path.name)
    yield
    logger.info("application_stopped")


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)
app.middleware("http")(logging_middleware)


@app.exception_handler(FintechBackendException)
async def fintech_exception_handler(
    _request: Request,
    exc: FintechBackendException,
) -> JSONResponse:
    """Return safe JSON responses for application exceptions."""

    str(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.error_message},
    )


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(users_router)
app.include_router(utils_router)
