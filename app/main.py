"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import APP_TITLE, APP_VERSION
from app.db import Base, engine
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.users import router as users_router
from app.routers.utils import router as utils_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables when the app starts."""

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(utils_router)
