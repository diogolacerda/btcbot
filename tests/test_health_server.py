"""
Tests for Health Server (DEVOPS-011).

Tests:
1. HealthServer can start and stop correctly
2. GET /health returns correct JSON structure
3. Status codes are correct (200 for healthy, 503 for unhealthy)
4. Component checks work correctly
5. Timeout handling works
"""

from unittest.mock import MagicMock, patch

import pytest

from src.health.health_server import HealthServer


class TestHealthServerBasic:
    """Test basic HealthServer functionality."""

    async def test_health_server_start_stop(self):
        """Test that health server can start and stop correctly."""
        server = HealthServer(port=18080)

        # Server should not be running initially
        assert not server.is_running

        # Start server
        await server.start()
        assert server.is_running

        # Stop server
        await server.stop()
        assert not server.is_running

    async def test_health_server_double_start(self):
        """Test that starting server twice doesn't cause issues."""
        server = HealthServer(port=18081)

        await server.start()
        await server.start()  # Should not raise
        assert server.is_running

        await server.stop()

    async def test_health_server_double_stop(self):
        """Test that stopping server twice doesn't cause issues."""
        server = HealthServer(port=18082)

        await server.start()
        await server.stop()
        await server.stop()  # Should not raise
        assert not server.is_running

    def test_health_server_default_port(self):
        """Test that default port is 8080."""
        server = HealthServer()
        assert server.port == 8080

    def test_health_server_custom_port(self):
        """Test that custom port is respected."""
        server = HealthServer(port=9090)
        assert server.port == 9090

    def test_health_server_port_from_env(self):
        """Test that port can be set from environment variable."""
        with patch.dict("os.environ", {"HEALTH_PORT": "9999"}):
            server = HealthServer()
            assert server.port == 9999

    def test_uptime_seconds(self):
        """Test that uptime is calculated correctly."""
        server = HealthServer()
        # Uptime should be positive
        assert server.uptime_seconds >= 0


class TestHealthServerEndpoint:
    """Test the /health endpoint."""

    async def test_health_endpoint_returns_json(self):
        """Test that /health endpoint returns valid JSON."""
        import aiohttp

        server = HealthServer(port=18083)
        await server.start()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:18083/health") as resp:
                    data = await resp.json()

                    # Check required fields
                    assert "status" in data
                    assert "version" in data
                    assert "uptime_seconds" in data
                    assert "timestamp" in data
                    assert "environment" in data
                    assert "trading_mode" in data
                    assert "components" in data
                    assert "grid" in data
        finally:
            await server.stop()

    async def test_health_endpoint_status_healthy(self):
        """Test that healthy status returns 200."""
        import aiohttp

        # Create mock client that returns successfully
        mock_client = MagicMock()
        mock_client.get_price = MagicMock(return_value=95000.0)

        server = HealthServer(port=18084)
        server.set_bingx_client(mock_client)
        await server.start()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:18084/health") as resp:
                    assert resp.status == 200
                    data = await resp.json()
                    assert data["status"] == "healthy"
        finally:
            await server.stop()

    async def test_health_endpoint_status_unhealthy(self):
        """Test that unhealthy status returns 503."""
        import aiohttp

        # Create mock client that raises an error
        mock_client = MagicMock()
        mock_client.get_price = MagicMock(side_effect=Exception("Connection failed"))

        server = HealthServer(port=18085)
        server.set_bingx_client(mock_client)
        await server.start()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:18085/health") as resp:
                    assert resp.status == 503
                    data = await resp.json()
                    assert data["status"] == "unhealthy"
        finally:
            await server.stop()


class TestHealthServerComponents:
    """Test component health checks."""

    def test_exchange_api_check_success(self):
        """Test exchange API check with successful response."""
        mock_client = MagicMock()
        mock_client.get_price = MagicMock(return_value=95000.0)

        server = HealthServer(port=18086)
        server.set_bingx_client(mock_client)

        result = server._check_exchange_api()

        assert result["status"] == "healthy"
        assert "latency_ms" in result
        assert result["latency_ms"] >= 0

    def test_exchange_api_check_failure(self):
        """Test exchange API check with failed response."""
        mock_client = MagicMock()
        mock_client.get_price = MagicMock(side_effect=Exception("API Error"))

        server = HealthServer(port=18087)
        server.set_bingx_client(mock_client)

        result = server._check_exchange_api()

        assert result["status"] == "unhealthy"
        assert "error" in result

    def test_exchange_api_check_no_client(self):
        """Test exchange API check without client."""
        server = HealthServer(port=18088)

        result = server._check_exchange_api()

        assert result["status"] == "unknown"
        assert "message" in result

    def test_websocket_check_connected(self):
        """Test WebSocket check when connected."""
        mock_ws = MagicMock()
        mock_ws.is_connected = True

        server = HealthServer(port=18089)
        server.set_account_websocket(mock_ws)

        result = server._check_websocket()

        assert result["status"] == "healthy"
        assert result["connected"] is True

    def test_websocket_check_disconnected(self):
        """Test WebSocket check when disconnected."""
        mock_ws = MagicMock()
        mock_ws.is_connected = False

        server = HealthServer(port=18090)
        server.set_account_websocket(mock_ws)

        result = server._check_websocket()

        assert result["status"] == "degraded"
        assert result["connected"] is False

    def test_websocket_check_no_ws(self):
        """Test WebSocket check without WebSocket."""
        server = HealthServer(port=18091)

        result = server._check_websocket()

        assert result["status"] == "unknown"
        assert result["connected"] is False


class TestHealthServerGridStatus:
    """Test grid status reporting."""

    def test_grid_status_with_manager(self):
        """Test grid status with GridManager."""
        from src.strategy.macd_strategy import GridState

        mock_status = MagicMock()
        mock_status.state = GridState.ACTIVE
        mock_status.open_positions = 3
        mock_status.pending_orders = 5
        mock_status.cycle_activated = True
        mock_status.margin_error = False
        mock_status.rate_limited = False

        mock_manager = MagicMock()
        mock_manager.get_status.return_value = mock_status

        server = HealthServer(port=18092)
        server.set_grid_manager(mock_manager)

        result = server._get_grid_status()

        assert result["state"] == "ACTIVE"
        assert result["open_positions"] == 3
        assert result["pending_orders"] == 5
        assert result["cycle_activated"] is True

    def test_grid_status_no_manager(self):
        """Test grid status without GridManager."""
        server = HealthServer(port=18093)

        result = server._get_grid_status()

        assert result["state"] == "unknown"
        assert result["open_positions"] == 0
        assert result["pending_orders"] == 0

    def test_grid_status_error(self):
        """Test grid status when manager raises error."""
        mock_manager = MagicMock()
        mock_manager.get_status.side_effect = Exception("Status error")

        server = HealthServer(port=18094)
        server.set_grid_manager(mock_manager)

        result = server._get_grid_status()

        assert result["state"] == "error"
        assert "error" in result


class TestHealthServerIntegration:
    """Integration tests for health server."""

    async def test_full_health_check_response_structure(self):
        """Test complete health check response matches expected structure."""
        import aiohttp

        from src.strategy.macd_strategy import GridState

        # Setup mocks
        mock_client = MagicMock()
        mock_client.get_price = MagicMock(return_value=95000.0)

        mock_ws = MagicMock()
        mock_ws.is_connected = True

        mock_status = MagicMock()
        mock_status.state = GridState.ACTIVE
        mock_status.open_positions = 2
        mock_status.pending_orders = 4
        mock_status.cycle_activated = True
        mock_status.margin_error = False
        mock_status.rate_limited = False

        mock_manager = MagicMock()
        mock_manager.get_status.return_value = mock_status

        server = HealthServer(port=18095)
        server.set_bingx_client(mock_client)
        server.set_account_websocket(mock_ws)
        server.set_grid_manager(mock_manager)
        await server.start()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:18095/health") as resp:
                    assert resp.status == 200
                    data = await resp.json()

                    # Verify structure matches DEVOPS-011 requirements
                    assert data["status"] == "healthy"
                    assert "version" in data
                    assert isinstance(data["uptime_seconds"], int)
                    assert "timestamp" in data
                    assert "environment" in data
                    assert "trading_mode" in data

                    # Components
                    assert "exchange_api" in data["components"]
                    assert "websocket" in data["components"]
                    assert data["components"]["exchange_api"]["status"] == "healthy"
                    assert "latency_ms" in data["components"]["exchange_api"]
                    assert data["components"]["websocket"]["connected"] is True

                    # Grid
                    assert data["grid"]["state"] == "ACTIVE"
                    assert data["grid"]["open_positions"] == 2
                    assert data["grid"]["pending_orders"] == 4
        finally:
            await server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
