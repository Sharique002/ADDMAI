"""Tests for health and readiness probes conforming to Sections 7, 8, 9, 17 of Stage 1.1."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# Ensure apps/api is on sys.path
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app


class TestHealthAndReadiness(unittest.TestCase):
    """Test health liveness, truthful readiness probing, and error scenarios."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_liveness_endpoint_contract(self) -> None:
        """GET /api/v1/health returns HTTP 200 and exact {'status': 'healthy'}."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_readiness_all_dependencies_ready(self) -> None:
        """Test Case 1: When all services are reachable -> HTTP 200 & status = 'ready'."""
        with patch("app.services.health.check_tcp_connection", return_value=True):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ready")
            self.assertEqual(data["dependencies"]["postgres"]["status"], "ready")
            self.assertEqual(data["dependencies"]["redis"]["status"], "ready")
            self.assertEqual(data["dependencies"]["minio"]["status"], "ready")
            self.assertIn("timestamp", data)

    def test_readiness_postgres_unavailable(self) -> None:
        """Test Case 2: When PostgreSQL is down -> HTTP 503 & postgres.status = 'not_ready'."""
        def mock_tcp_probe(host: str, port: int, timeout: float = 0.5) -> bool:
            # PostgreSQL is on 5432
            return port != 5432

        with patch("app.services.health.check_tcp_connection", side_effect=mock_tcp_probe):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data["status"], "not_ready")
            self.assertEqual(data["dependencies"]["postgres"]["status"], "not_ready")
            self.assertEqual(data["dependencies"]["redis"]["status"], "ready")
            self.assertEqual(data["dependencies"]["minio"]["status"], "ready")

    def test_readiness_redis_unavailable(self) -> None:
        """Test Case 3: When Redis is down -> HTTP 503 & redis.status = 'not_ready'."""
        def mock_tcp_probe(host: str, port: int, timeout: float = 0.5) -> bool:
            # Redis is on 6379
            return port != 6379

        with patch("app.services.health.check_tcp_connection", side_effect=mock_tcp_probe):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data["status"], "not_ready")
            self.assertEqual(data["dependencies"]["redis"]["status"], "not_ready")
            self.assertEqual(data["dependencies"]["postgres"]["status"], "ready")

    def test_readiness_minio_unavailable(self) -> None:
        """Test Case 4: When MinIO is down -> HTTP 503 & minio.status = 'not_ready'."""
        def mock_tcp_probe(host: str, port: int, timeout: float = 0.5) -> bool:
            # MinIO is on 9000
            return port != 9000

        with patch("app.services.health.check_tcp_connection", side_effect=mock_tcp_probe):
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data["status"], "not_ready")
            self.assertEqual(data["dependencies"]["minio"]["status"], "not_ready")

    def test_readiness_malformed_configuration(self) -> None:
        """Test Case 5: Malformed config is reported as not_ready with no secret leakage."""
        with patch.object(settings, "DATABASE_URL", "invalid://///broken-uri"):
            with patch("app.services.health.check_tcp_connection", return_value=True):
                response = self.client.get("/api/v1/ready")
                self.assertEqual(response.status_code, 503)
                data = response.json()
                self.assertEqual(data["status"], "not_ready")
                self.assertEqual(data["dependencies"]["postgres"]["status"], "not_ready")

                # Verify no sensitive keywords or URLs in response payload (Section 9)
                content = response.text
                self.assertNotIn("password", content.lower())
                self.assertNotIn("broken-uri", content)

    def test_no_credentials_leaked_in_readiness(self) -> None:
        """Verify readiness probe does not expose connection strings, passwords, or keys."""
        with patch("app.services.health.check_tcp_connection", return_value=True):
            response = self.client.get("/api/v1/ready")
            raw_text = response.text
            self.assertNotIn("addmai_dev_password", raw_text)
            self.assertNotIn("minioadmin", raw_text)
            self.assertNotIn("postgresql+asyncpg", raw_text)


if __name__ == "__main__":
    unittest.main()
