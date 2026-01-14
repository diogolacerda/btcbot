"""
Integration tests for filter API endpoints.

Tests the HTTP endpoints in HealthServer for managing filters.
"""

from unittest.mock import MagicMock

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from src.filters.base import Filter, FilterState
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.health.health_server import HealthServer


class DummyFilter(Filter):
    """Dummy filter for testing."""

    def __init__(self, name: str = "test", description: str = "Test Filter"):
        super().__init__(name, description)
        self._allow_trade = True

    def should_allow_trade(self) -> bool:
        return self.enabled and self._allow_trade

    def get_state(self) -> FilterState:
        return FilterState(
            enabled=self.enabled,
            description=self.description,
            details={"allow_trade": self._allow_trade},
        )


class TestFilterAPI(AioHTTPTestCase):
    """Test filter API endpoints."""

    async def get_application(self):
        """Create test application with HealthServer routes."""
        # Reset registry
        registry = FilterRegistry()
        registry.clear()

        # Register test filters
        f1 = DummyFilter("filter1", "Test Filter 1")
        f2 = DummyFilter("filter2", "Test Filter 2")
        registry.register(f1)
        registry.register(f2)

        # Create health server
        self.health_server = HealthServer(port=8888)

        # Create app manually to access routes
        app = web.Application()
        app.router.add_get("/filters", self.health_server._handle_get_filters)
        app.router.add_post("/filters/{filter_name}", self.health_server._handle_toggle_filter)
        app.router.add_post("/filters/disable-all", self.health_server._handle_disable_all)
        app.router.add_post("/filters/enable-all", self.health_server._handle_enable_all)

        return app

    async def tearDownAsync(self):
        """Cleanup after tests."""
        registry = FilterRegistry()
        registry.clear()

    async def test_get_filters(self):
        """Test GET /filters returns all filter states."""
        resp = await self.client.get("/filters")
        assert resp.status == 200

        data = await resp.json()
        assert "filters" in data
        assert "all_enabled" in data
        assert "any_enabled" in data
        assert "total_count" in data
        assert "enabled_count" in data

        # Both filters enabled by default
        assert data["total_count"] == 2
        assert data["enabled_count"] == 2
        assert data["all_enabled"] is True
        assert data["any_enabled"] is True

        # Check individual filters
        assert "filter1" in data["filters"]
        assert "filter2" in data["filters"]
        assert data["filters"]["filter1"]["enabled"] is True
        assert data["filters"]["filter2"]["enabled"] is True

    async def test_toggle_filter_disable(self):
        """Test POST /filters/{name} to disable a filter."""
        resp = await self.client.post(
            "/filters/filter1",
            json={"enabled": False},
        )
        assert resp.status == 200

        data = await resp.json()
        assert data["filter"] == "filter1"
        assert data["enabled"] is False
        assert "disabled" in data["message"]

        # Verify state changed
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["filters"]["filter1"]["enabled"] is False
        assert data["enabled_count"] == 1

    async def test_toggle_filter_enable(self):
        """Test POST /filters/{name} to enable a filter."""
        # First disable it
        await self.client.post("/filters/filter1", json={"enabled": False})

        # Then enable it
        resp = await self.client.post(
            "/filters/filter1",
            json={"enabled": True},
        )
        assert resp.status == 200

        data = await resp.json()
        assert data["filter"] == "filter1"
        assert data["enabled"] is True
        assert "enabled" in data["message"]

        # Verify state changed
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["filters"]["filter1"]["enabled"] is True
        assert data["enabled_count"] == 2

    async def test_toggle_nonexistent_filter(self):
        """Test toggling nonexistent filter returns 404."""
        resp = await self.client.post(
            "/filters/nonexistent",
            json={"enabled": False},
        )
        assert resp.status == 404

        data = await resp.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_toggle_filter_invalid_body(self):
        """Test toggle with invalid JSON body returns 400."""
        # Invalid JSON
        resp = await self.client.post(
            "/filters/filter1",
            data="not json",
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data

    async def test_toggle_filter_missing_enabled(self):
        """Test toggle without 'enabled' field returns 400."""
        resp = await self.client.post(
            "/filters/filter1",
            json={"something": "else"},
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data
        assert "enabled" in data["error"].lower()

    async def test_disable_all_filters(self):
        """Test POST /filters/disable-all."""
        resp = await self.client.post("/filters/disable-all")
        assert resp.status == 200

        data = await resp.json()
        assert "message" in data
        assert "disabled" in data["message"].lower()
        assert "filters" in data
        assert len(data["filters"]) == 2

        # Verify all disabled
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 0
        assert data["all_enabled"] is False
        assert data["any_enabled"] is False

    async def test_enable_all_filters(self):
        """Test POST /filters/enable-all."""
        # First disable all
        await self.client.post("/filters/disable-all")

        # Then enable all
        resp = await self.client.post("/filters/enable-all")
        assert resp.status == 200

        data = await resp.json()
        assert "message" in data
        assert "enabled" in data["message"].lower()

        # Verify all enabled
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 2
        assert data["all_enabled"] is True
        assert data["any_enabled"] is True

    async def test_filter_workflow(self):
        """Test complete workflow: disable one, disable all, enable all."""
        # Start: both enabled
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 2

        # Disable filter1
        await self.client.post("/filters/filter1", json={"enabled": False})
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 1
        assert data["filters"]["filter1"]["enabled"] is False
        assert data["filters"]["filter2"]["enabled"] is True

        # Disable all
        await self.client.post("/filters/disable-all")
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 0

        # Enable all (restores both to enabled)
        await self.client.post("/filters/enable-all")
        resp = await self.client.get("/filters")
        data = await resp.json()
        assert data["enabled_count"] == 2
        assert data["filters"]["filter1"]["enabled"] is True
        assert data["filters"]["filter2"]["enabled"] is True


def test_filter_state_persistence():
    """Test that filter state changes persist within registry."""
    # Reset registry
    registry = FilterRegistry()
    registry.clear()

    # Register filter
    f1 = DummyFilter("persist_test", "Persistence Test")
    registry.register(f1)

    # Initially enabled
    assert f1.enabled is True

    # Disable via registry
    registry.disable_filter("persist_test")
    assert f1.enabled is False

    # Get same filter from registry
    retrieved = registry.get_filter("persist_test")
    assert retrieved is f1
    assert retrieved.enabled is False

    # Enable via registry
    registry.enable_filter("persist_test")
    assert f1.enabled is True
    assert retrieved.enabled is True

    # Cleanup
    registry.clear()


def test_filter_state_volatility():
    """Test that filter state is volatile (resets on registry clear)."""
    # Reset registry
    registry = FilterRegistry()
    registry.clear()

    # Register and disable filter
    f1 = DummyFilter("volatile_test", "Volatility Test")
    registry.register(f1)
    registry.disable_filter("volatile_test")

    assert f1.enabled is False

    # Clear registry (simulates restart)
    registry.clear()

    # Re-register (simulates startup)
    f2 = DummyFilter("volatile_test", "Volatility Test")
    registry.register(f2)

    # Should be enabled by default (no persistence)
    assert f2.enabled is True

    # Cleanup
    registry.clear()


class TestMACDTriggerAPI(AioHTTPTestCase):
    """Test MACD trigger API endpoint."""

    async def get_application(self):
        """Create test application with MACD trigger route."""
        # Reset registry
        registry = FilterRegistry()
        registry.clear()

        # Create mock MACD filter
        mock_macd = MagicMock(spec=MACDFilter)
        mock_macd.name = "macd"
        mock_macd.description = "MACD Filter"
        mock_macd.enabled = True
        mock_macd.set_trigger = MagicMock(return_value=True)
        mock_macd.get_state = MagicMock(
            return_value=FilterState(
                enabled=True,
                description="MACD Filter",
                details={"trigger_activated": True},
            )
        )
        registry.register(mock_macd)

        # Create health server
        self.health_server = HealthServer(port=8889)
        self.mock_macd = mock_macd

        # Create app with MACD trigger route
        app = web.Application()
        app.router.add_post("/filters/macd/trigger", self.health_server._handle_macd_trigger)

        return app

    async def tearDownAsync(self):
        """Cleanup after tests."""
        registry = FilterRegistry()
        registry.clear()

    async def test_macd_trigger_activate(self):
        """Test POST /filters/macd/trigger with activated=true."""
        resp = await self.client.post(
            "/filters/macd/trigger",
            json={"activated": True},
        )
        assert resp.status == 200

        data = await resp.json()
        assert data["activated"] is True
        assert data["persisted"] is True
        assert "activated successfully" in data["message"]
        assert "details" in data

        # Verify set_trigger was called with True
        self.mock_macd.set_trigger.assert_called_once_with(True)

    async def test_macd_trigger_deactivate(self):
        """Test POST /filters/macd/trigger with activated=false."""
        resp = await self.client.post(
            "/filters/macd/trigger",
            json={"activated": False},
        )
        assert resp.status == 200

        data = await resp.json()
        assert data["activated"] is False
        assert data["persisted"] is True
        assert "deactivated successfully" in data["message"]

        # Verify set_trigger was called with False
        self.mock_macd.set_trigger.assert_called_once_with(False)

    async def test_macd_trigger_invalid_json(self):
        """Test trigger endpoint with invalid JSON returns 400."""
        resp = await self.client.post(
            "/filters/macd/trigger",
            data="not json",
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data
        assert "Invalid JSON" in data["error"]

    async def test_macd_trigger_missing_activated(self):
        """Test trigger endpoint without 'activated' field returns 400."""
        resp = await self.client.post(
            "/filters/macd/trigger",
            json={"something": "else"},
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data
        assert "activated" in data["error"]

    async def test_macd_trigger_activation_fails(self):
        """Test trigger endpoint when set_trigger fails."""
        # Make set_trigger return False
        self.mock_macd.set_trigger.return_value = False

        resp = await self.client.post(
            "/filters/macd/trigger",
            json={"activated": True},
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data
        assert "Failed to activate" in data["error"]

    async def test_macd_trigger_filter_not_found(self):
        """Test trigger endpoint when MACD filter is not registered."""
        # Create a new app without MACD filter
        registry = FilterRegistry()
        registry.clear()

        health_server = HealthServer(port=8890)

        app = web.Application()
        app.router.add_post("/filters/macd/trigger", health_server._handle_macd_trigger)

        # Replace app
        self.app = app

        resp = await self.client.post(
            "/filters/macd/trigger",
            json={"activated": True},
        )
        assert resp.status == 404

        data = await resp.json()
        assert "error" in data
        assert "not found" in data["error"].lower()
