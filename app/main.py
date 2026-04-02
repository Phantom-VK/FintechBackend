from fastapi import FastAPI

from app.config import APP_TITLE, APP_VERSION
from app.db import Base, engine
from app import models
from app.routers.health import router as health_router
from app.routers.utils import router as utils_router

app = FastAPI(title=APP_TITLE, version=APP_VERSION)
app.include_router(health_router)
app.include_router(utils_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

