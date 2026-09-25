"""Tests for health and readiness probes (Section 20 of Stage 1)."""

import os
import sys
from pathlib import Path
import unittest

# Ensure apps/api is importable
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

os.environ["APP_ENV"] = "testing"

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_TESTCLIENT = True
except ImportError:  # pragma: no cover
    HAS_TESTCLIENT = False


class TestHealthEndpoint(unittest.TestCase):
    """Test health and readiness probe functionality."""

    def test_health_endpoint_response(self) -> None:
        """Test GET /api/v1/health returns HTTP 200 and {'status': 'healthy'}."""
        if HAS_TESTCLIENT and app:
            client = TestClient(app)
            response = client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "healthy"})
        else:
            # Fallback direct function verification
            from app.api.v1.health import get_health
            result = get_health()
            self.assertEqual(result, {"status": "healthy"})

    def test_ready_endpoint_response(self) -> None:
        """Test GET /api/v1/ready returns expected readiness status."""
        if HAS_TESTCLIENT and app:
            client = TestClient(app)
            response = client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("status", data)
            self.assertIn("dependencies", data)
            self.assertIn("postgres", data["dependencies"])
            self.assertIn("redis", data["dependencies"])
            self.assertIn("minio", data["dependencies"])
        else:
            from app.api.v1.health import get_readiness
            result = get_readiness()
            self.assertIn("status", result)
            self.assertIn("dependencies", result)

    def test_configuration_identity(self) -> None:
        """Verify Stage 1 configuration metadata."""
        from app.core.config import settings
        self.assertEqual(settings.APP_NAME, "ADDMAI API")
        self.assertEqual(settings.APP_VERSION, "0.1.0")

    def test_security_sanitization(self) -> None:
        """Verify filename sanitization prevents path traversal."""
        from app.core.security import sanitize_filename
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("valid_image.png"), "valid_image.png")


if __name__ == "__main__":
    unittest.main()
