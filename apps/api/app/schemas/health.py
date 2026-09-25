"""Health and readiness response schemas conforming to Sections 4, 5, 9 of Stage 1/1.1."""

from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness health response schema: HTTP 200 with {'status': 'healthy'}."""
    status: str = Field(default="healthy", description="Application liveness status")


class DependencyDetail(BaseModel):
    """Sanitized individual downstream dependency status (no credentials or hosts)."""
    configured: bool = Field(..., description="Whether connection configuration is defined")
    status: str = Field(..., description="Readiness status of dependency: ready or not_ready")


class ReadyResponse(BaseModel):
    """Readiness probe response schema indicating overall system readiness."""
    status: str = Field(..., description="Overall readiness: ready or not_ready")
    dependencies: Dict[str, DependencyDetail] = Field(..., description="Map of infrastructure dependencies")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of inspection")
