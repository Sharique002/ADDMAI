"""API v1 Router definitions."""

from fastapi import APIRouter
from .health import router as health_router
from .media import router as media_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(media_router, prefix="/media", tags=["Media"])

__all__ = ["api_router"]

