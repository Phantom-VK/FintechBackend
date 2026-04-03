"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models as model_registry
from app.config import APP_TITLE, APP_VERSION
from app.database import Base, engine
from app.routers.dashboard import router as dashboard_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.transactions import router as transactions_router
from app.routers.users import router as users_router
from app.routers.utils import router as utils_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables when the app starts."""

    _ = model_registry
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(users_router)
app.include_router(utils_router)
