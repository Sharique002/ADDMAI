"""Thin HTTP route definitions for health and readiness probes (Stage 1.1).

Conforms to Section 7 (Health/Readiness Refactor) and Section 9 (Contract).
Delegates dependency inspection logic entirely to HealthService.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.health import health_service

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service Liveness Probe",
    description="Returns HTTP 200 and {'status': 'healthy'} without exposing internal info.",
    response_model=HealthResponse,
)
async def get_health() -> Dict[str, str]:
    """Stage 1/1.1 Liveness Probe: Returns HTTP 200 with {'status': 'healthy'}."""
    return health_service.get_liveness()


@router.get(
    "/ready",
    summary="Service Readiness Probe",
    description="Verifies downstream infrastructure (PostgreSQL, Redis, MinIO) connectivity.",
    response_model=ReadyResponse,
    responses={
        200: {"description": "All infrastructure dependencies are ready", "model": ReadyResponse},
        503: {"description": "One or more infrastructure dependencies are not ready", "model": ReadyResponse},
    },
)
async def get_readiness(response: Response) -> Dict[str, Any]:
    """Stage 1.1 Truthful Readiness Probe.

    Returns HTTP 200 when all configured dependencies are ready.
    Returns HTTP 503 when any configured dependency is not ready.
    """
    all_ready, dependencies = health_service.check_readiness(settings)

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "not_ready"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "ready"

    return {
        "status": overall_status,
        "dependencies": dependencies,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
