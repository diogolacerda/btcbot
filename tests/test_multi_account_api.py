"""
Integration tests for multi-account API endpoints.

Tests the HTTP endpoints in HealthServer for managing configurations
across multiple accounts using account_id path parameters.
"""

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.database.models.grid_config import GridConfig
from src.database.models.trading_config import TradingConfig
from src.health.health_server import HealthServer


class TestMultiAccountTradingConfigAPI(AioHTTPTestCase):
    """Test multi-account trading config API endpoints."""

    def get_application(self):
        """Create test application with HealthServer routes."""
        # Create mock repository
        self.trading_config_repo_mock = MagicMock()
        self.trading_config_repo_mock.get_by_account = MagicMock()
        self.trading_config_repo_mock.create_or_update = MagicMock()

        # Create test accounts
        self.account_id_1 = uuid4()
        self.account_id_2 = uuid4()

        # Create default trading configs for both accounts
        from datetime import UTC, datetime

        self.config_1 = TradingConfig(
            account_id=self.account_id_1,
            symbol="BTC-USDT",
            leverage=10,
            order_size_usdt=Decimal("100.00"),
            margin_mode="CROSSED",
            take_profit_percent=Decimal("0.50"),
        )
        self.config_1.created_at = datetime.now(UTC)
        self.config_1.updated_at = datetime.now(UTC)

        self.config_2 = TradingConfig(
            account_id=self.account_id_2,
            symbol="ETH-USDT",
            leverage=20,
            order_size_usdt=Decimal("200.00"),
            margin_mode="ISOLATED",
            take_profit_percent=Decimal("1.00"),
        )
        self.config_2.created_at = datetime.now(UTC)
        self.config_2.updated_at = datetime.now(UTC)

        # Configure mocks
        def get_by_account_side_effect(account_id):
            if account_id == self.account_id_1:
                return self.config_1
            elif account_id == self.account_id_2:
                return self.config_2
            return None

        self.trading_config_repo_mock.get_by_account.side_effect = get_by_account_side_effect

        # Create health server with mocked repo
        self.health_server = HealthServer(
            port=8888,
            trading_config_repo=self.trading_config_repo_mock,
        )

        # Create app with multi-account routes
        app = web.Application()
        app.router.add_get(
            "/api/accounts/{account_id}/configs/trading",
            self.health_server._handle_get_trading_config_multi,
        )
        app.router.add_put(
            "/api/accounts/{account_id}/configs/trading",
            self.health_server._handle_put_trading_config_multi,
        )
        app.router.add_patch(
            "/api/accounts/{account_id}/configs/trading",
            self.health_server._handle_patch_trading_config_multi,
        )

        return app

    @unittest_run_loop
    def test_get_trading_config_multi_account_1(self):
        """Test GET with account_id returns correct config for account 1."""
        resp = self.client.get(f"/api/accounts/{self.account_id_1}/configs/trading")
        assert resp.status == 200

        data = resp.json()
        assert data["account_id"] == str(self.account_id_1)
        assert data["symbol"] == "BTC-USDT"
        assert data["leverage"] == 10
        assert data["order_size_usdt"] == 100.00
        assert data["take_profit_percent"] == 0.50

    @unittest_run_loop
    def test_get_trading_config_multi_account_2(self):
        """Test GET with account_id returns correct config for account 2."""
        resp = self.client.get(f"/api/accounts/{self.account_id_2}/configs/trading")
        assert resp.status == 200

        data = resp.json()
        assert data["account_id"] == str(self.account_id_2)
        assert data["symbol"] == "ETH-USDT"
        assert data["leverage"] == 20
        assert data["order_size_usdt"] == 200.00
        assert data["take_profit_percent"] == 1.00

    @unittest_run_loop
    def test_get_trading_config_invalid_uuid(self):
        """Test GET with invalid UUID returns 400."""
        resp = self.client.get("/api/accounts/invalid-uuid/configs/trading")
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "Invalid account_id" in data["error"]

    @unittest_run_loop
    def test_get_trading_config_not_found(self):
        """Test GET with non-existent account returns 404."""
        non_existent_id = uuid4()
        resp = self.client.get(f"/api/accounts/{non_existent_id}/configs/trading")
        assert resp.status == 404

        data = resp.json()
        assert "error" in data
        assert "No trading configuration found" in data["error"]

    @unittest_run_loop
    def test_put_trading_config_multi_account(self):
        """Test PUT with account_id updates config for specific account."""
        # Configure mock to return updated config
        from datetime import UTC, datetime

        updated_config = TradingConfig(
            account_id=self.account_id_1,
            symbol="BTC-USDT",
            leverage=15,
            order_size_usdt=Decimal("150.00"),
            margin_mode="CROSSED",
            take_profit_percent=Decimal("0.75"),
        )
        updated_config.created_at = datetime.now(UTC)
        updated_config.updated_at = datetime.now(UTC)
        self.trading_config_repo_mock.create_or_update.return_value = updated_config

        resp = self.client.put(
            f"/api/accounts/{self.account_id_1}/configs/trading",
            json={
                "symbol": "BTC-USDT",
                "leverage": 15,
                "order_size_usdt": 150.00,
                "margin_mode": "CROSSED",
                "take_profit_percent": 0.75,
            },
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Trading configuration updated successfully"
        assert data["config"]["account_id"] == str(self.account_id_1)
        assert data["config"]["leverage"] == 15

    @unittest_run_loop
    def test_patch_trading_config_multi_account(self):
        """Test PATCH with account_id updates specific fields for account."""
        # Configure mock to return updated config
        from datetime import UTC, datetime

        updated_config = TradingConfig(
            account_id=self.account_id_2,
            symbol="ETH-USDT",
            leverage=25,  # Updated
            order_size_usdt=Decimal("200.00"),  # Unchanged
            margin_mode="ISOLATED",
            take_profit_percent=Decimal("1.00"),
        )
        updated_config.created_at = datetime.now(UTC)
        updated_config.updated_at = datetime.now(UTC)
        self.trading_config_repo_mock.create_or_update.return_value = updated_config

        resp = self.client.patch(
            f"/api/accounts/{self.account_id_2}/configs/trading",
            json={"leverage": 25},
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Trading configuration updated successfully"
        assert "updated_fields" in data
        assert "leverage" in data["updated_fields"]
        assert data["config"]["account_id"] == str(self.account_id_2)
        assert data["config"]["leverage"] == 25


class TestMultiAccountGridConfigAPI(AioHTTPTestCase):
    """Test multi-account grid config API endpoints."""

    def get_application(self):
        """Create test application with HealthServer routes."""
        # Create mock repository
        self.grid_config_repo_mock = MagicMock()
        self.grid_config_repo_mock.get_or_create = MagicMock()
        self.grid_config_repo_mock.save_config = MagicMock()
        self.grid_config_repo_mock.to_dict = MagicMock()

        # Create test accounts
        self.account_id_1 = uuid4()
        self.account_id_2 = uuid4()

        # Create default grid configs
        self.grid_config_1 = GridConfig(
            account_id=self.account_id_1,
            spacing_type="fixed",
            spacing_value=Decimal("100.0"),
            range_percent=Decimal("5.0"),
            max_total_orders=10,
            anchor_mode="none",
            anchor_value=Decimal("100.0"),
        )
        self.grid_config_2 = GridConfig(
            account_id=self.account_id_2,
            spacing_type="percentage",
            spacing_value=Decimal("2.5"),
            range_percent=Decimal("10.0"),
            max_total_orders=20,
            anchor_mode="hundred",
            anchor_value=Decimal("50.0"),
        )

        # Configure mocks
        def get_or_create_side_effect(account_id):
            if account_id == self.account_id_1:
                return self.grid_config_1
            elif account_id == self.account_id_2:
                return self.grid_config_2
            return GridConfig(account_id=account_id)

        self.grid_config_repo_mock.get_or_create.side_effect = get_or_create_side_effect

        def to_dict_side_effect(config):
            return {
                "spacing_type": config.spacing_type,
                "spacing_value": float(config.spacing_value),
                "range_percent": float(config.range_percent),
                "max_total_orders": config.max_total_orders,
                "anchor_mode": config.anchor_mode,
                "anchor_value": float(config.anchor_value),
            }

        self.grid_config_repo_mock.to_dict.side_effect = to_dict_side_effect

        # Create health server with mocked repo
        self.health_server = HealthServer(
            port=8888,
            grid_config_repo=self.grid_config_repo_mock,
        )

        # Create app with multi-account routes
        app = web.Application()
        app.router.add_get(
            "/api/accounts/{account_id}/configs/grid",
            self.health_server._handle_get_grid_config_multi,
        )
        app.router.add_put(
            "/api/accounts/{account_id}/configs/grid",
            self.health_server._handle_put_grid_config_multi,
        )
        app.router.add_patch(
            "/api/accounts/{account_id}/configs/grid",
            self.health_server._handle_patch_grid_config_multi,
        )

        return app

    @unittest_run_loop
    def test_get_grid_config_multi_account_1(self):
        """Test GET with account_id returns correct config for account 1."""
        resp = self.client.get(f"/api/accounts/{self.account_id_1}/configs/grid")
        assert resp.status == 200

        data = resp.json()
        assert data["spacing_type"] == "fixed"
        assert data["spacing_value"] == 100.0
        assert data["range_percent"] == 5.0
        assert data["max_total_orders"] == 10

    @unittest_run_loop
    def test_get_grid_config_multi_account_2(self):
        """Test GET with account_id returns correct config for account 2."""
        resp = self.client.get(f"/api/accounts/{self.account_id_2}/configs/grid")
        assert resp.status == 200

        data = resp.json()
        assert data["spacing_type"] == "percentage"
        assert data["spacing_value"] == 2.5
        assert data["range_percent"] == 10.0
        assert data["max_total_orders"] == 20

    @unittest_run_loop
    def test_get_grid_config_invalid_uuid(self):
        """Test GET with invalid UUID returns 400."""
        resp = self.client.get("/api/accounts/not-a-uuid/configs/grid")
        assert resp.status == 400

        data = resp.json()
        assert "error" in data
        assert "Invalid account_id" in data["error"]

    @unittest_run_loop
    def test_put_grid_config_multi_account(self):
        """Test PUT with account_id updates config for specific account."""
        # Configure mock to return updated config
        updated_config = GridConfig(
            account_id=self.account_id_1,
            spacing_type="percentage",
            spacing_value=Decimal("3.0"),
            range_percent=Decimal("8.0"),
            max_total_orders=15,
            anchor_mode="hundred",
            anchor_value=Decimal("75.0"),
        )
        self.grid_config_repo_mock.save_config.return_value = updated_config

        resp = self.client.put(
            f"/api/accounts/{self.account_id_1}/configs/grid",
            json={
                "spacing_type": "percentage",
                "spacing_value": 3.0,
                "range_percent": 8.0,
                "max_total_orders": 15,
                "anchor_mode": "hundred",
                "anchor_value": 75.0,
            },
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Grid configuration updated successfully"

    @unittest_run_loop
    def test_patch_grid_config_multi_account(self):
        """Test PATCH with account_id updates specific fields."""
        # Configure mock to return updated config
        updated_config = GridConfig(
            account_id=self.account_id_2,
            spacing_type="percentage",
            spacing_value=Decimal("2.5"),
            range_percent=Decimal("12.0"),  # Updated
            max_total_orders=20,
            anchor_mode="hundred",
            anchor_value=Decimal("50.0"),
        )
        self.grid_config_repo_mock.save_config.return_value = updated_config

        resp = self.client.patch(
            f"/api/accounts/{self.account_id_2}/configs/grid",
            json={"range_percent": 12.0},
        )
        assert resp.status == 200

        data = resp.json()
        assert data["message"] == "Grid configuration updated successfully"
        assert "updated_fields" in data
        assert "range_percent" in data["updated_fields"]

    @unittest_run_loop
    def test_put_grid_config_invalid_account_id(self):
        """Test PUT with invalid account_id returns 400."""
        resp = self.client.put(
            "/api/accounts/bad-id/configs/grid",
            json={
                "spacing_type": "fixed",
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
        assert "Invalid account_id" in data["error"]
