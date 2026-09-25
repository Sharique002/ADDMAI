"""API v1 Router definitions."""

from fastapi import APIRouter
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])

__all__ = ["api_router"]
