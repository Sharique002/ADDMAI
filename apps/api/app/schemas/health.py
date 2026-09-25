"""Health and readiness response schemas."""

from typing import Any, Dict

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    HAS_PYDANTIC = False


if HAS_PYDANTIC:
    class HealthResponse(BaseModel):
        """Liveness health response schema matching Stage 1 specification."""
        status: str = Field(default="healthy", description="Application liveness status")

    class DependencyStatus(BaseModel):
        """Individual downstream dependency status."""
        configured: bool = Field(..., description="Whether the dependency has connection configuration")
        status: str = Field(..., description="Connectivity status of the dependency: ready, not_ready, or pending")

    class ReadyResponse(BaseModel):
        """Readiness probe response schema."""
        status: str = Field(..., description="Overall readiness status: ready or not_ready")
        dependencies: Dict[str, Any] = Field(..., description="Map of infrastructure dependencies")
        timestamp: str = Field(..., description="ISO 8601 UTC timestamp of check")

else:  # Fallback dataclass representations
    class HealthResponse:  # type: ignore
        def __init__(self, status: str = "healthy") -> None:
            self.status = status

        def dict(self) -> Dict[str, Any]:
            return {"status": self.status}

    class ReadyResponse:  # type: ignore
        def __init__(self, status: str, dependencies: Dict[str, Any], timestamp: str) -> None:
            self.status = status
            self.dependencies = dependencies
            self.timestamp = timestamp

        def dict(self) -> Dict[str, Any]:
            return {
                "status": self.status,
                "dependencies": self.dependencies,
                "timestamp": self.timestamp,
            }
