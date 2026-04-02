"""Utility routes."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["utils"])

BASE_DIR = Path(__file__).resolve().parents[2]
FAVICON_PATH = BASE_DIR / "static" / "favicon.ico"


@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve the favicon file."""

    return FileResponse(FAVICON_PATH)
