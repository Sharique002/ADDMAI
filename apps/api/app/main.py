"""Main FastAPI Application Entrypoint for ADDMAI API (Stage 1).

Conforms to Sections 3, 4, 18, 19 of Stage 1 specification.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

try:
    from fastapi import FastAPI, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False

from app import __version__
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.security import generate_request_id

logger = get_logger("addmai.api")


@asynccontextmanager
async def lifespan(app: Any) -> AsyncGenerator[None, None]:
    """Lifespan event handler for startup and shutdown."""
    setup_logging(service_name="ADDMAI-API", log_level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} v{__version__} [{settings.APP_ENV}]")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> Any:
    """Instantiate and configure the FastAPI application."""
    if not HAS_FASTAPI:
        return None

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Deepfake Detection & Media Authenticity Intelligence",
        version=__version__,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # CORS configuration (Section 19: Explicit development origins, no wildcard *)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request ID Middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> Any:
        req_id = request.headers.get("X-Request-ID") or generate_request_id()
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # Include API Routers
    from app.api.v1 import api_router
    if api_router:
        app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root health redirect / alias
    @app.get("/health", include_in_schema=False)
    async def root_health() -> Any:
        from app.api.v1.health import get_health
        return await get_health()

    return app


app = create_app()
