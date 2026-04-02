from fastapi import FastAPI

from app.config import APP_TITLE, APP_VERSION
from app.routers.health import router as health_router

app = FastAPI(title=APP_TITLE, version=APP_VERSION)
app.include_router(health_router)
