"""
Health Check Server for BTC Grid Bot.

Provides HTTP endpoint for health monitoring, used by:
- Docker healthcheck
- Portainer status monitoring
- Watchtower update verification

The server runs in parallel with the main bot loop using aiohttp.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aiohttp import web

from src.filters.registry import FilterRegistry
from src.utils.logger import main_logger

if TYPE_CHECKING:
    from src.client.bingx_client import BingXClient
    from src.client.websocket_client import BingXAccountWebSocket
    from src.grid.grid_manager import GridManager

# Version info - should match project version
__version__ = "1.0.0"


class HealthServer:
    """
    Lightweight HTTP server for health checks.

    Provides:
    - GET /health - Full health status with component checks
    - Status codes:
        - 200: All components healthy
        - 503: One or more components unhealthy
    """

    def __init__(
        self,
        port: int | None = None,
        grid_manager: GridManager | None = None,
        bingx_client: BingXClient | None = None,
        account_ws: BingXAccountWebSocket | None = None,
    ):
        """
        Initialize the health server.

        Args:
            port: HTTP port to listen on (defaults to HEALTH_PORT env var or 8080)
            grid_manager: GridManager instance for status checks
            bingx_client: BingX client for API health checks
            account_ws: WebSocket client for connection status
        """
        self.port = port or int(os.getenv("HEALTH_PORT", "8080"))
        self._grid_manager = grid_manager
        self._bingx_client = bingx_client
        self._account_ws = account_ws

        self._start_time = time.time()
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._running = False

        # Component check timeout in seconds
        self._check_timeout = 5.0

        # Filter registry (singleton)
        self._filter_registry = FilterRegistry()

    def set_grid_manager(self, grid_manager: GridManager) -> None:
        """Set the grid manager reference for status checks."""
        self._grid_manager = grid_manager

    def set_bingx_client(self, client: BingXClient) -> None:
        """Set the BingX client reference for API checks."""
        self._bingx_client = client

    def set_account_websocket(self, ws: BingXAccountWebSocket) -> None:
        """Set the WebSocket client reference for connection checks."""
        self._account_ws = ws

    @property
    def uptime_seconds(self) -> float:
        """Get server uptime in seconds."""
        return time.time() - self._start_time

    async def start(self) -> None:
        """Start the health check HTTP server."""
        if self._running:
            main_logger.warning("Health server already running")
            return

        self._app = web.Application()
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/filters", self._handle_get_filters)
        self._app.router.add_post("/filters/{filter_name}", self._handle_toggle_filter)
        self._app.router.add_post("/filters/disable-all", self._handle_disable_all)
        self._app.router.add_post("/filters/enable-all", self._handle_enable_all)

        self._runner = web.AppRunner(self._app, access_log=None)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await self._site.start()

        self._running = True
        main_logger.info(f"Health server started on port {self.port}")

    async def stop(self) -> None:
        """Stop the health check HTTP server."""
        if not self._running:
            return

        if self._runner:
            await self._runner.cleanup()

        self._running = False
        main_logger.info("Health server stopped")

    async def _handle_health(self, request: web.Request) -> web.Response:
        """
        Handle GET /health request.

        Returns JSON with health status of all components.
        Status code 200 if healthy, 503 if any component is unhealthy.
        """
        # Log only at DEBUG level to avoid noise
        main_logger.debug(f"Health check request from {request.remote}")

        try:
            # Check all components with timeout
            health_data = await asyncio.wait_for(
                self._get_health_status(),
                timeout=self._check_timeout,
            )

            # Determine overall status
            is_healthy = health_data["status"] == "healthy"
            status_code = 200 if is_healthy else 503

            return web.json_response(health_data, status=status_code)

        except TimeoutError:
            main_logger.warning("Health check timed out")
            return web.json_response(
                {
                    "status": "unhealthy",
                    "error": "Health check timed out",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                status=503,
            )
        except Exception as e:
            main_logger.error(f"Health check error: {e}")
            return web.json_response(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                status=503,
            )

    async def _get_health_status(self) -> dict[str, Any]:
        """
        Get comprehensive health status.

        Returns:
            Dict with health status of all components
        """
        components: dict[str, dict[str, Any]] = {}
        overall_healthy = True

        # Check exchange API
        api_status = await self._check_exchange_api()
        components["exchange_api"] = api_status
        if api_status["status"] != "healthy":
            overall_healthy = False

        # Check WebSocket connection
        ws_status = self._check_websocket()
        components["websocket"] = ws_status
        # WebSocket is not critical for health - bot can work with polling
        # So we don't set overall_healthy = False here

        # Get grid status
        grid_status = self._get_grid_status()

        # Get environment info
        environment = os.getenv("ENVIRONMENT", os.getenv("TRADING_MODE", "unknown"))
        trading_mode = os.getenv("TRADING_MODE", "demo")

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "version": __version__,
            "uptime_seconds": int(self.uptime_seconds),
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": environment,
            "trading_mode": trading_mode,
            "components": components,
            "grid": grid_status,
        }

    async def _check_exchange_api(self) -> dict[str, Any]:
        """
        Check BingX exchange API health.

        Returns:
            Dict with status and latency
        """
        if not self._bingx_client:
            return {
                "status": "unknown",
                "message": "Client not initialized",
            }

        try:
            start_time = time.time()
            # Simple price check to verify API connectivity
            symbol = os.getenv("SYMBOL", "BTC-USDT")
            await self._bingx_client.get_price(symbol)
            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "status": "healthy",
                "latency_ms": latency_ms,
            }
        except Exception as e:
            main_logger.warning(f"Exchange API health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_websocket(self) -> dict[str, Any]:
        """
        Check WebSocket connection status.

        Returns:
            Dict with connection status
        """
        if not self._account_ws:
            return {
                "status": "unknown",
                "connected": False,
                "message": "WebSocket not initialized",
            }

        is_connected = self._account_ws.is_connected

        return {
            "status": "healthy" if is_connected else "degraded",
            "connected": is_connected,
        }

    def _get_grid_status(self) -> dict[str, Any]:
        """
        Get current grid trading status.

        Returns:
            Dict with grid state and order counts
        """
        if not self._grid_manager:
            return {
                "state": "unknown",
                "open_positions": 0,
                "pending_orders": 0,
            }

        try:
            status = self._grid_manager.get_status()
            return {
                "state": status.state.value.upper(),
                "open_positions": status.open_positions,
                "pending_orders": status.pending_orders,
                "cycle_activated": status.cycle_activated,
                "margin_error": status.margin_error,
                "rate_limited": status.rate_limited,
            }
        except Exception as e:
            main_logger.warning(f"Error getting grid status: {e}")
            return {
                "state": "error",
                "error": str(e),
            }

    async def _handle_get_filters(self, request: web.Request) -> web.Response:
        """
        Handle GET /filters request.

        Returns JSON with state of all filters.
        """
        main_logger.debug(f"GET /filters request from {request.remote}")

        try:
            states = self._filter_registry.get_all_states()
            return web.json_response(states, status=200)

        except Exception as e:
            main_logger.error(f"Error getting filter states: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_toggle_filter(self, request: web.Request) -> web.Response:
        """
        Handle POST /filters/{filter_name} request.

        Expects JSON body: {"enabled": true/false}
        Toggles the specified filter on/off.
        """
        filter_name = request.match_info["filter_name"]
        main_logger.debug(f"POST /filters/{filter_name} request from {request.remote}")

        try:
            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": 'Invalid JSON body. Expected: {"enabled": true/false}'},
                    status=400,
                )

            if "enabled" not in data:
                return web.json_response(
                    {"error": "Missing 'enabled' field in request body"},
                    status=400,
                )

            enabled = bool(data["enabled"])

            # Check if filter exists
            if not self._filter_registry.get_filter(filter_name):
                return web.json_response(
                    {"error": f"Filter '{filter_name}' not found"},
                    status=404,
                )

            # Toggle filter
            if enabled:
                success = self._filter_registry.enable_filter(filter_name)
            else:
                success = self._filter_registry.disable_filter(filter_name)

            if not success:
                return web.json_response(
                    {"error": f"Failed to update filter '{filter_name}'"},
                    status=500,
                )

            # Get updated state
            filter_instance = self._filter_registry.get_filter(filter_name)
            state = filter_instance.get_state() if filter_instance else None

            response = {
                "filter": filter_name,
                "enabled": enabled,
                "message": f"Filter {filter_name} {'enabled' if enabled else 'disabled'}",
            }

            if state:
                response["details"] = state.details

            return web.json_response(response, status=200)

        except Exception as e:
            main_logger.error(f"Error toggling filter: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_disable_all(self, request: web.Request) -> web.Response:
        """
        Handle POST /filters/disable-all request.

        Disables all registered filters.
        """
        main_logger.debug(f"POST /filters/disable-all request from {request.remote}")

        try:
            self._filter_registry.disable_all()

            return web.json_response(
                {
                    "message": "All filters disabled",
                    "filters": self._filter_registry.list_filters(),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error disabling all filters: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_enable_all(self, request: web.Request) -> web.Response:
        """
        Handle POST /filters/enable-all request.

        Enables all registered filters (restores default state).
        """
        main_logger.debug(f"POST /filters/enable-all request from {request.remote}")

        try:
            self._filter_registry.enable_all()

            return web.json_response(
                {
                    "message": "All filters enabled",
                    "filters": self._filter_registry.list_filters(),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error enabling all filters: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    @property
    def is_running(self) -> bool:
        """Check if health server is running."""
        return self._running
