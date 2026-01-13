"""
Integration tests for grid config API endpoints.

Tests the HTTP endpoints in HealthServer for managing grid configuration.
"""

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.database.models.grid_config import GridConfig
from src.health.health_server import HealthServer


class TestGridConfigAPI(AioHTTPTestCase):
    """Test grid config API endpoints."""

    def get_application(self):
        """Create test application with HealthServer routes."""
        # Create mock repositories
        self.grid_config_repo_mock = MagicMock()
        self.grid_config_repo_mock.get_or_create = MagicMock()
        self.grid_config_repo_mock.save_config = MagicMock()
        self.grid_config_repo_mock.to_dict = MagicMock()

        # Create account ID for testing
        self.account_id = uuid4()

        # Create default grid config for tests
        self.default_grid_config = GridConfig(
            account_id=self.account_id,
            spacing_type="fixed",
            spacing_value=Decimal("100.0"),
            range_percent=Decimal("5.0"),
            max_total_orders=10,
            anchor_mode="none",
            anchor_value=Decimal("100.0"),
        )

        # Configure mocks
        self.grid_config_repo_mock.get_or_create.return_value = self.default_grid_config
        self.grid_config_repo_mock.to_dict.return_value = {
            "id": str(self.default_grid_config.id),
            "account_id": str(self.default_grid_config.account_id),
            "spacing_type": "fixed",
            "spacing_value": 100.0,
            "range_percent": 5.0,
            "max_total_orders": 10,
            "anchor_mode": "none",
            "anchor_value": 100.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # Create health server with mocked repo
        self.health_server = HealthServer(
            port=8888,
            grid_config_repo=self.grid_config_repo_mock,
            account_id=self.account_id,
        )

        # Create app manually to access routes
        app = web.Application()
        app.router.add_get("/api/configs/grid", self.health_server._handle_get_grid_config)
        app.router.add_put("/api/configs/grid", self.health_server._handle_put_grid_config)
        app.router.add_patch("/api/configs/grid", self.health_server._handle_patch_grid_config)

        return app

    @unittest_run_loop
    def test_get_grid_config_success(self):
        """Test GET /api/configs/grid returns config successfully."""
        resp = self.client.get("/api/configs/grid")
        assert resp.status == 200

        data = resp.json()
        assert data["spacing_type"] == "fixed"
        assert data["spacing_value"] == 100.0
        assert data["range_percent"] == 5.0
        assert data["max_total_orders"] == 10
        assert data["anchor_mode"] == "none"
        assert data["anchor_value"] == 100.0

        # Verify repo was called
        self.grid_config_repo_mock.get_or_create.assert_called_once_with(self.account_id)

    @unittest_run_loop
    def test_put_grid_config_success(self):
        """Test PUT /api/configs/grid updates all fields successfully."""
        # Configure mock to return updated config
        updated_config = GridConfig(
            account_id=self.account_id,
            spacing_type="percentage",
            spacing_value=Decimal("2.5"),
            range_percent=Decimal("10.0"),
            max_total_orders=20,
            anchor_mode="hundred",
            anchor_value=Decimal("50.0"),
        )
        self.grid_config_repo_mock.save_config.return_value = updated_config
        self.grid_config_repo_mock.to_dict.return_value = {
            "id": str(updated_config.id),
            "account_id": str(updated_config.account_id),
            "spacing_type": "percentage",
            "spacing_value": 2.5,
            "range_percent": 10.0,
            "max_total_orders": 20,
            "anchor_mode": "hundred",
            "anchor_value": 50.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:01Z",
        }

        # Send PUT request
        resp = self.client.put(
            "/api/configs/grid",
            json={
                "spacing_type": "percentage",
                "spacing_value": 2.5,
                "range_percent": 10.0,
                "max_total_orders": 20,
                "anchor_mode": "hundred",
                "anchor_value": 50.0,
            },
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Grid configuration updated successfully"
        assert data["config"]["spacing_type"] == "percentage"
        assert data["config"]["spacing_value"] == 2.5

        # Verify repo was called with correct params
        self.grid_config_repo_mock.save_config.assert_called_once()

    @unittest_run_loop
    def test_put_grid_config_missing_fields(self):
        """Test PUT /api/configs/grid returns 400 when fields are missing."""
        resp = self.client.put(
            "/api/configs/grid",
            json={
                "spacing_type": "fixed",
                # Missing other required fields
            },
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "Missing required fields" in data["error"]

    @unittest_run_loop
    def test_put_grid_config_invalid_spacing_type(self):
        """Test PUT /api/configs/grid validates spacing_type."""
        resp = self.client.put(
            "/api/configs/grid",
            json={
                "spacing_type": "invalid",
                "spacing_value": 100.0,
                "range_percent": 5.0,
                "max_total_orders": 10,
                "anchor_mode": "none",
                "anchor_value": 100.0,
            },
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "spacing_type must be" in data["error"]

    @unittest_run_loop
    def test_put_grid_config_invalid_anchor_mode(self):
        """Test PUT /api/configs/grid validates anchor_mode."""
        resp = self.client.put(
            "/api/configs/grid",
            json={
                "spacing_type": "fixed",
                "spacing_value": 100.0,
                "range_percent": 5.0,
                "max_total_orders": 10,
                "anchor_mode": "invalid",
                "anchor_value": 100.0,
            },
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "anchor_mode must be" in data["error"]

    @unittest_run_loop
    def test_put_grid_config_negative_values(self):
        """Test PUT /api/configs/grid rejects negative values."""
        resp = self.client.put(
            "/api/configs/grid",
            json={
                "spacing_type": "fixed",
                "spacing_value": -100.0,
                "range_percent": 5.0,
                "max_total_orders": 10,
                "anchor_mode": "none",
                "anchor_value": 100.0,
            },
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "must be positive" in data["error"]

    @unittest_run_loop
    def test_patch_grid_config_partial_update(self):
        """Test PATCH /api/configs/grid updates only provided fields."""
        # Configure mock to return updated config
        updated_config = GridConfig(
            account_id=self.account_id,
            spacing_type="fixed",
            spacing_value=Decimal("200.0"),  # Updated
            range_percent=Decimal("5.0"),  # Not updated
            max_total_orders=10,  # Not updated
            anchor_mode="none",
            anchor_value=Decimal("100.0"),
        )
        self.grid_config_repo_mock.save_config.return_value = updated_config
        self.grid_config_repo_mock.to_dict.return_value = {
            "id": str(updated_config.id),
            "account_id": str(updated_config.account_id),
            "spacing_type": "fixed",
            "spacing_value": 200.0,
            "range_percent": 5.0,
            "max_total_orders": 10,
            "anchor_mode": "none",
            "anchor_value": 100.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:01Z",
        }

        # Send PATCH request with only spacing_value
        resp = self.client.patch(
            "/api/configs/grid",
            json={"spacing_value": 200.0},
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Grid configuration updated successfully"
        assert "updated_fields" in data
        assert "spacing_value" in data["updated_fields"]
        assert data["config"]["spacing_value"] == 200.0

    @unittest_run_loop
    def test_patch_grid_config_no_fields(self):
        """Test PATCH /api/configs/grid returns 400 when no fields provided."""
        resp = self.client.patch("/api/configs/grid", json={})
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "No fields provided" in data["error"]

    @unittest_run_loop
    def test_patch_grid_config_invalid_value(self):
        """Test PATCH /api/configs/grid validates field values."""
        resp = self.client.patch(
            "/api/configs/grid",
            json={"max_total_orders": -5},
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "must be positive" in data["error"]

    @unittest_run_loop
    def test_patch_grid_config_invalid_type(self):
        """Test PATCH /api/configs/grid validates spacing_type in PATCH."""
        resp = self.client.patch(
            "/api/configs/grid",
            json={"spacing_type": "invalid_type"},
        )
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "spacing_type must be" in data["error"]
