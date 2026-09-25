"""Root test runner for API health endpoint (Section 20)."""

import os
import sys
from pathlib import Path
import unittest

# Point sys.path to apps/api
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

os.environ["APP_ENV"] = "testing"

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_TESTCLIENT = True
except ImportError:  # pragma: no cover
    HAS_TESTCLIENT = False


class TestAPIHealth(unittest.TestCase):
    """Test health endpoint conforming to Section 20."""

    def test_health_success(self) -> None:
        """GET /api/v1/health returns HTTP 200 and {'status': 'healthy'}."""
        if HAS_TESTCLIENT and app:
            client = TestClient(app)
            response = client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "healthy"})
        else:
            from app.api.v1.health import get_health
            result = get_health()
            self.assertEqual(result, {"status": "healthy"})

    def test_readiness_structure(self) -> None:
        """GET /api/v1/ready returns structured dependency status."""
        from app.api.v1.health import probe_dependencies
        deps = probe_dependencies()
        self.assertIn("postgres", deps)
        self.assertIn("redis", deps)
        self.assertIn("minio", deps)


if __name__ == "__main__":
    unittest.main()
