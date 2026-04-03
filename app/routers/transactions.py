"""Transaction routes."""

from fastapi import APIRouter


router = APIRouter(prefix="/transactions", tags=["transactions"])
