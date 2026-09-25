"""Root test runner for API health and readiness endpoints (Stage 1.1).

Conforms to Section 8, 9, 17 of Stage 1.1 specification.
"""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# Point sys.path to apps/api
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from fastapi.testclient import TestClient
from app.main import app


class TestAPIHealth(unittest.TestCase):
    """Test health and readiness endpoints via root test runner."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_success(self) -> None:
        """GET /api/v1/health returns HTTP 200 and {'status': 'healthy'}."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_readiness_healthy_when_probes_pass(self) -> None:
        """GET /api/v1/ready returns HTTP 200 when dependency probes succeed."""
        with patch("app.services.health.check_tcp_connection", return_value=True):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ready")
            self.assertEqual(data["dependencies"]["postgres"]["status"], "ready")
            self.assertEqual(data["dependencies"]["redis"]["status"], "ready")
            self.assertEqual(data["dependencies"]["minio"]["status"], "ready")

    def test_readiness_503_when_probe_fails(self) -> None:
        """GET /api/v1/ready returns HTTP 503 when any dependency probe fails."""
        with patch("app.services.health.check_tcp_connection", return_value=False):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data["status"], "not_ready")


if __name__ == "__main__":
    unittest.main()
