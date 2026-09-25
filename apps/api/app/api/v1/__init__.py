"""API v1 router."""

try:
    from fastapi import APIRouter
    from .health import router as health_router

    api_router = APIRouter()
    api_router.include_router(health_router, tags=["Health"])
except ImportError:  # pragma: no cover
    api_router = None  # type: ignore

__all__ = ["api_router"]
