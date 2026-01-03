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
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from aiohttp import web

from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.utils.logger import main_logger

if TYPE_CHECKING:
    from src.client.bingx_client import BingXClient
    from src.client.websocket_client import BingXAccountWebSocket
    from src.database.repositories.grid_config_repository import GridConfigRepository
    from src.database.repositories.trading_config_repository import TradingConfigRepository
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
        trading_config_repo: TradingConfigRepository | None = None,
        grid_config_repo: GridConfigRepository | None = None,
        account_id: UUID | None = None,
    ):
        """
        Initialize the health server.

        Args:
            port: HTTP port to listen on (defaults to HEALTH_PORT env var or 8080)
            grid_manager: GridManager instance for status checks
            bingx_client: BingX client for API health checks
            account_ws: WebSocket client for connection status
            trading_config_repo: Repository for trading config persistence
            grid_config_repo: Repository for grid config persistence
            account_id: Account ID for config operations
        """
        self.port = port or int(os.getenv("HEALTH_PORT", "8080"))
        self._grid_manager = grid_manager
        self._bingx_client = bingx_client
        self._account_ws = account_ws
        self._trading_config_repo = trading_config_repo
        self._grid_config_repo = grid_config_repo
        self._account_id = account_id

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

    def set_trading_config_repo(self, repo: TradingConfigRepository) -> None:
        """Set the trading config repository reference for API operations."""
        self._trading_config_repo = repo

    def set_grid_config_repo(self, repo: GridConfigRepository) -> None:
        """Set the grid config repository reference for API operations."""
        self._grid_config_repo = repo

    def set_account_id(self, account_id: UUID) -> None:
        """Set the account ID for config operations."""
        self._account_id = account_id

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
        self._app.router.add_post("/api/macd/activate", self._handle_activate_macd)
        self._app.router.add_post("/api/macd/deactivate", self._handle_deactivate_macd)
        self._app.router.add_post("/filters/macd/trigger", self._handle_macd_trigger)
        # Single-account routes (backward compatibility)
        self._app.router.add_get("/api/configs/trading", self._handle_get_trading_config)
        self._app.router.add_put("/api/configs/trading", self._handle_put_trading_config)
        self._app.router.add_patch("/api/configs/trading", self._handle_patch_trading_config)
        self._app.router.add_get("/api/configs/grid", self._handle_get_grid_config)
        self._app.router.add_put("/api/configs/grid", self._handle_put_grid_config)
        self._app.router.add_patch("/api/configs/grid", self._handle_patch_grid_config)

        # Multi-account routes (with account_id in path)
        self._app.router.add_get(
            "/api/accounts/{account_id}/configs/trading",
            self._handle_get_trading_config_multi,
        )
        self._app.router.add_put(
            "/api/accounts/{account_id}/configs/trading",
            self._handle_put_trading_config_multi,
        )
        self._app.router.add_patch(
            "/api/accounts/{account_id}/configs/trading",
            self._handle_patch_trading_config_multi,
        )
        self._app.router.add_get(
            "/api/accounts/{account_id}/configs/grid",
            self._handle_get_grid_config_multi,
        )
        self._app.router.add_put(
            "/api/accounts/{account_id}/configs/grid",
            self._handle_put_grid_config_multi,
        )
        self._app.router.add_patch(
            "/api/accounts/{account_id}/configs/grid",
            self._handle_patch_grid_config_multi,
        )

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

    async def _handle_activate_macd(self, request: web.Request) -> web.Response:
        """
        Handle POST /api/macd/activate request.

        Manually activates the MACD cycle and trigger, and persists the state to database.
        """
        main_logger.debug(f"POST /api/macd/activate request from {request.remote}")

        try:
            # Get MACD filter
            macd_filter = self._filter_registry.get_filter("macd")
            if not macd_filter:
                return web.json_response(
                    {"error": "MACD filter not found"},
                    status=404,
                )

            # Check if filter is MACDFilter (type check)
            if not isinstance(macd_filter, MACDFilter):
                return web.json_response(
                    {"error": "MACD filter does not support manual activation"},
                    status=500,
                )

            # Activate via filter (which will trigger strategy.manual_activate())
            success = macd_filter.set_trigger(True)

            if not success:
                return web.json_response(
                    {
                        "error": "Failed to activate MACD (might be in INACTIVE state)",
                        "message": "Cannot activate in INACTIVE state (market falling)",
                    },
                    status=400,
                )

            # Get updated state
            state = macd_filter.get_state()

            return web.json_response(
                {
                    "message": "MACD cycle and trigger activated successfully",
                    "activated": True,
                    "persisted": True,
                    "details": state.details,
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error activating MACD: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_deactivate_macd(self, request: web.Request) -> web.Response:
        """
        Handle POST /api/macd/deactivate request.

        Manually deactivates the MACD cycle and trigger, and persists the state to database.
        """
        main_logger.debug(f"POST /api/macd/deactivate request from {request.remote}")

        try:
            # Get MACD filter
            macd_filter = self._filter_registry.get_filter("macd")
            if not macd_filter:
                return web.json_response(
                    {"error": "MACD filter not found"},
                    status=404,
                )

            # Check if filter is MACDFilter (type check)
            if not isinstance(macd_filter, MACDFilter):
                return web.json_response(
                    {"error": "MACD filter does not support manual deactivation"},
                    status=500,
                )

            # Deactivate via filter
            success = macd_filter.set_trigger(False)

            if not success:
                return web.json_response(
                    {"error": "Failed to deactivate MACD"},
                    status=400,
                )

            # Get updated state
            state = macd_filter.get_state()

            return web.json_response(
                {
                    "message": "MACD cycle and trigger deactivated successfully",
                    "activated": False,
                    "persisted": True,
                    "details": state.details,
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error deactivating MACD: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_macd_trigger(self, request: web.Request) -> web.Response:
        """
        Handle POST /filters/macd/trigger request.

        Expects JSON body: {"activated": true/false}
        Activates or deactivates the MACD cycle and trigger.
        """
        main_logger.debug(f"POST /filters/macd/trigger request from {request.remote}")

        try:
            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": 'Invalid JSON body. Expected: {"activated": true/false}'},
                    status=400,
                )

            if "activated" not in data:
                return web.json_response(
                    {"error": "Missing 'activated' field in request body"},
                    status=400,
                )

            activated = bool(data["activated"])

            # Get MACD filter
            macd_filter = self._filter_registry.get_filter("macd")
            if not macd_filter:
                return web.json_response(
                    {"error": "MACD filter not found"},
                    status=404,
                )

            # Check if filter is MACDFilter (type check)
            if not isinstance(macd_filter, MACDFilter):
                return web.json_response(
                    {"error": "MACD filter does not support trigger control"},
                    status=500,
                )

            # Activate or deactivate via filter
            success = macd_filter.set_trigger(activated)

            if not success:
                error_msg = (
                    "Failed to activate MACD (might be in INACTIVE state)"
                    if activated
                    else "Failed to deactivate MACD"
                )
                return web.json_response(
                    {"error": error_msg},
                    status=400,
                )

            # Get updated state
            state = macd_filter.get_state()

            action = "activated" if activated else "deactivated"
            return web.json_response(
                {
                    "message": f"MACD cycle and trigger {action} successfully",
                    "activated": activated,
                    "persisted": True,
                    "details": state.details,
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error controlling MACD trigger: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_get_trading_config(self, request: web.Request) -> web.Response:
        """
        Handle GET /api/configs/trading request.

        Returns current trading configuration for the account.
        """
        main_logger.debug(f"GET /api/configs/trading request from {request.remote}")

        try:
            if not self._trading_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Trading config repository or account ID not configured"},
                    status=500,
                )

            # Get current config
            config = await self._trading_config_repo.get_by_account(self._account_id)

            if not config:
                return web.json_response(
                    {"error": "No trading configuration found for this account"},
                    status=404,
                )

            # Convert to dict for JSON response
            return web.json_response(
                {
                    "id": str(config.id),
                    "account_id": str(config.account_id),
                    "symbol": config.symbol,
                    "leverage": config.leverage,
                    "order_size_usdt": float(config.order_size_usdt),
                    "margin_mode": config.margin_mode,
                    "take_profit_percent": float(config.take_profit_percent),
                    "tp_dynamic_enabled": config.tp_dynamic_enabled,
                    "tp_base_percent": float(config.tp_base_percent),
                    "tp_min_percent": float(config.tp_min_percent),
                    "tp_max_percent": float(config.tp_max_percent),
                    "tp_safety_margin": float(config.tp_safety_margin),
                    "tp_check_interval_min": config.tp_check_interval_min,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat(),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error getting trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_put_trading_config(self, request: web.Request) -> web.Response:
        """
        Handle PUT /api/configs/trading request.

        Updates all trading configuration fields.
        Expects JSON body with all required fields.
        """
        main_logger.debug(f"PUT /api/configs/trading request from {request.remote}")

        try:
            if not self._trading_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Trading config repository or account ID not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            # Validate required fields
            required_fields = [
                "symbol",
                "leverage",
                "order_size_usdt",
                "margin_mode",
                "take_profit_percent",
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                return web.json_response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=400,
                )

            # Validate field types and values
            try:
                symbol = str(data["symbol"])
                leverage = int(data["leverage"])
                order_size_usdt = Decimal(str(data["order_size_usdt"]))
                margin_mode = str(data["margin_mode"])
                take_profit_percent = Decimal(str(data["take_profit_percent"]))

                # Validate ranges
                if leverage < 1 or leverage > 125:
                    return web.json_response(
                        {"error": "Leverage must be between 1 and 125"},
                        status=400,
                    )

                if order_size_usdt <= 0:
                    return web.json_response(
                        {"error": "Order size must be positive"},
                        status=400,
                    )

                if margin_mode not in ["CROSSED", "ISOLATED"]:
                    return web.json_response(
                        {"error": "Margin mode must be CROSSED or ISOLATED"},
                        status=400,
                    )

                if take_profit_percent <= 0 or take_profit_percent > 10:
                    return web.json_response(
                        {"error": "Take profit percent must be between 0 and 10"},
                        status=400,
                    )

            except (ValueError, TypeError) as e:
                return web.json_response(
                    {"error": f"Invalid field value: {e}"},
                    status=400,
                )

            # Update config
            config = await self._trading_config_repo.create_or_update(
                self._account_id,
                symbol=symbol,
                leverage=leverage,
                order_size_usdt=order_size_usdt,
                margin_mode=margin_mode,
                take_profit_percent=take_profit_percent,
            )

            main_logger.info(f"Trading config updated: {config}")

            return web.json_response(
                {
                    "message": "Trading configuration updated successfully",
                    "config": {
                        "id": str(config.id),
                        "account_id": str(config.account_id),
                        "symbol": config.symbol,
                        "leverage": config.leverage,
                        "order_size_usdt": float(config.order_size_usdt),
                        "margin_mode": config.margin_mode,
                        "take_profit_percent": float(config.take_profit_percent),
                        "tp_dynamic_enabled": config.tp_dynamic_enabled,
                        "tp_base_percent": float(config.tp_base_percent),
                        "tp_min_percent": float(config.tp_min_percent),
                        "tp_max_percent": float(config.tp_max_percent),
                        "tp_safety_margin": float(config.tp_safety_margin),
                        "tp_check_interval_min": config.tp_check_interval_min,
                        "updated_at": config.updated_at.isoformat(),
                    },
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_patch_trading_config(self, request: web.Request) -> web.Response:
        """
        Handle PATCH /api/configs/trading request.

        Updates specific trading configuration fields.
        Only provided fields will be updated.
        """
        main_logger.debug(f"PATCH /api/configs/trading request from {request.remote}")

        try:
            if not self._trading_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Trading config repository or account ID not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            if not data:
                return web.json_response(
                    {"error": "No fields provided to update"},
                    status=400,
                )

            # Build kwargs with validated values
            kwargs: dict[str, str | int | Decimal] = {}

            if "symbol" in data:
                kwargs["symbol"] = str(data["symbol"])

            if "leverage" in data:
                leverage = int(data["leverage"])
                if leverage < 1 or leverage > 125:
                    return web.json_response(
                        {"error": "Leverage must be between 1 and 125"},
                        status=400,
                    )
                kwargs["leverage"] = leverage

            if "order_size_usdt" in data:
                order_size = Decimal(str(data["order_size_usdt"]))
                if order_size <= 0:
                    return web.json_response(
                        {"error": "Order size must be positive"},
                        status=400,
                    )
                kwargs["order_size_usdt"] = order_size

            if "margin_mode" in data:
                margin_mode = str(data["margin_mode"])
                if margin_mode not in ["CROSSED", "ISOLATED"]:
                    return web.json_response(
                        {"error": "Margin mode must be CROSSED or ISOLATED"},
                        status=400,
                    )
                kwargs["margin_mode"] = margin_mode

            if "take_profit_percent" in data:
                tp_percent = Decimal(str(data["take_profit_percent"]))
                if tp_percent <= 0 or tp_percent > 10:
                    return web.json_response(
                        {"error": "Take profit percent must be between 0 and 10"},
                        status=400,
                    )
                kwargs["take_profit_percent"] = tp_percent

            # Dynamic TP fields (BE-035)
            if "tp_dynamic_enabled" in data:
                kwargs["tp_dynamic_enabled"] = bool(data["tp_dynamic_enabled"])

            if "tp_base_percent" in data:
                tp_base = Decimal(str(data["tp_base_percent"]))
                if tp_base <= 0:
                    return web.json_response(
                        {"error": "TP base percent must be greater than 0"},
                        status=400,
                    )
                kwargs["tp_base_percent"] = tp_base

            if "tp_min_percent" in data:
                tp_min = Decimal(str(data["tp_min_percent"]))
                if tp_min <= 0:
                    return web.json_response(
                        {"error": "TP min percent must be greater than 0"},
                        status=400,
                    )
                kwargs["tp_min_percent"] = tp_min

            if "tp_max_percent" in data:
                tp_max = Decimal(str(data["tp_max_percent"]))
                if tp_max <= 0:
                    return web.json_response(
                        {"error": "TP max percent must be greater than 0"},
                        status=400,
                    )
                kwargs["tp_max_percent"] = tp_max

            if "tp_safety_margin" in data:
                tp_safety = Decimal(str(data["tp_safety_margin"]))
                if tp_safety < 0:
                    return web.json_response(
                        {"error": "TP safety margin must be non-negative"},
                        status=400,
                    )
                kwargs["tp_safety_margin"] = tp_safety

            if "tp_check_interval_min" in data:
                tp_interval = int(data["tp_check_interval_min"])
                if tp_interval <= 0:
                    return web.json_response(
                        {"error": "TP check interval must be greater than 0"},
                        status=400,
                    )
                kwargs["tp_check_interval_min"] = tp_interval

            # Validate TP constraints after all fields are parsed
            tp_min_val: Decimal | None = kwargs.get("tp_min_percent")  # type: ignore[assignment]
            tp_base_val: Decimal | None = kwargs.get("tp_base_percent")  # type: ignore[assignment]
            tp_max_val: Decimal | None = kwargs.get("tp_max_percent")  # type: ignore[assignment]

            # If any TP percent fields are being updated, validate the complete set
            if tp_min_val is not None or tp_base_val is not None or tp_max_val is not None:
                # Get current config to fill in missing values
                current_config = await self._trading_config_repo.get_by_account(self._account_id)
                if current_config:
                    final_min: Decimal = (
                        tp_min_val if tp_min_val is not None else current_config.tp_min_percent
                    )
                    final_base: Decimal = (
                        tp_base_val if tp_base_val is not None else current_config.tp_base_percent
                    )
                    final_max: Decimal = (
                        tp_max_val if tp_max_val is not None else current_config.tp_max_percent
                    )

                    # Validate: min <= base <= max
                    if not (final_min <= final_base <= final_max):
                        return web.json_response(
                            {"error": "TP percentages must satisfy: min <= base <= max"},
                            status=400,
                        )

            # Update config
            config = await self._trading_config_repo.create_or_update(
                self._account_id,
                **kwargs,  # type: ignore[arg-type]
            )

            main_logger.info(f"Trading config updated (partial): {list(kwargs.keys())}")

            return web.json_response(
                {
                    "message": "Trading configuration updated successfully",
                    "updated_fields": list(kwargs.keys()),
                    "config": {
                        "id": str(config.id),
                        "account_id": str(config.account_id),
                        "symbol": config.symbol,
                        "leverage": config.leverage,
                        "order_size_usdt": float(config.order_size_usdt),
                        "margin_mode": config.margin_mode,
                        "take_profit_percent": float(config.take_profit_percent),
                        "tp_dynamic_enabled": config.tp_dynamic_enabled,
                        "tp_base_percent": float(config.tp_base_percent),
                        "tp_min_percent": float(config.tp_min_percent),
                        "tp_max_percent": float(config.tp_max_percent),
                        "tp_safety_margin": float(config.tp_safety_margin),
                        "tp_check_interval_min": config.tp_check_interval_min,
                        "updated_at": config.updated_at.isoformat(),
                    },
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_get_grid_config(self, request: web.Request) -> web.Response:
        """
        Handle GET /api/configs/grid request.

        Returns current grid configuration for the account.
        """
        main_logger.debug(f"GET /api/configs/grid request from {request.remote}")

        try:
            if not self._grid_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Grid config repository or account ID not configured"},
                    status=500,
                )

            # Get current config (or create with defaults if doesn't exist)
            config = await self._grid_config_repo.get_or_create(self._account_id)

            # Convert to dict for JSON response
            return web.json_response(
                self._grid_config_repo.to_dict(config),
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error getting grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_put_grid_config(self, request: web.Request) -> web.Response:
        """
        Handle PUT /api/configs/grid request.

        Updates all grid configuration fields.
        Expects JSON body with all required fields.
        """
        main_logger.debug(f"PUT /api/configs/grid request from {request.remote}")

        try:
            if not self._grid_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Grid config repository or account ID not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            # Validate required fields
            required_fields = [
                "spacing_type",
                "spacing_value",
                "range_percent",
                "max_total_orders",
                "anchor_mode",
                "anchor_value",
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                return web.json_response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=400,
                )

            # Validate field types and values
            try:
                spacing_type = str(data["spacing_type"])
                spacing_value = Decimal(str(data["spacing_value"]))
                range_percent = Decimal(str(data["range_percent"]))
                max_total_orders = int(data["max_total_orders"])
                anchor_mode = str(data["anchor_mode"])
                anchor_value = Decimal(str(data["anchor_value"]))

                # Validate spacing_type
                if spacing_type not in ["fixed", "percentage"]:
                    return web.json_response(
                        {"error": "spacing_type must be 'fixed' or 'percentage'"},
                        status=400,
                    )

                # Validate positive values
                if spacing_value <= 0:
                    return web.json_response(
                        {"error": "spacing_value must be positive"},
                        status=400,
                    )

                if range_percent <= 0:
                    return web.json_response(
                        {"error": "range_percent must be positive"},
                        status=400,
                    )

                if max_total_orders <= 0:
                    return web.json_response(
                        {"error": "max_total_orders must be positive"},
                        status=400,
                    )

                # Validate anchor_mode
                if anchor_mode not in ["none", "hundred"]:
                    return web.json_response(
                        {"error": "anchor_mode must be 'none' or 'hundred'"},
                        status=400,
                    )

                if anchor_value <= 0:
                    return web.json_response(
                        {"error": "anchor_value must be positive"},
                        status=400,
                    )

            except (ValueError, TypeError) as e:
                return web.json_response(
                    {"error": f"Invalid field value: {e}"},
                    status=400,
                )

            # Update config
            config = await self._grid_config_repo.save_config(
                self._account_id,
                spacing_type=spacing_type,
                spacing_value=spacing_value,
                range_percent=range_percent,
                max_total_orders=max_total_orders,
                anchor_mode=anchor_mode,
                anchor_value=anchor_value,
            )

            main_logger.info(f"Grid config updated: {config}")

            return web.json_response(
                {
                    "message": "Grid configuration updated successfully",
                    "config": self._grid_config_repo.to_dict(config),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_patch_grid_config(self, request: web.Request) -> web.Response:
        """
        Handle PATCH /api/configs/grid request.

        Updates specific grid configuration fields.
        Only provided fields will be updated.
        """
        main_logger.debug(f"PATCH /api/configs/grid request from {request.remote}")

        try:
            if not self._grid_config_repo or not self._account_id:
                return web.json_response(
                    {"error": "Grid config repository or account ID not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            if not data:
                return web.json_response(
                    {"error": "No fields provided to update"},
                    status=400,
                )

            # Build kwargs with validated values
            kwargs: dict[str, str | int | Decimal] = {}

            if "spacing_type" in data:
                spacing_type = str(data["spacing_type"])
                if spacing_type not in ["fixed", "percentage"]:
                    return web.json_response(
                        {"error": "spacing_type must be 'fixed' or 'percentage'"},
                        status=400,
                    )
                kwargs["spacing_type"] = spacing_type

            if "spacing_value" in data:
                spacing_value = Decimal(str(data["spacing_value"]))
                if spacing_value <= 0:
                    return web.json_response(
                        {"error": "spacing_value must be positive"},
                        status=400,
                    )
                kwargs["spacing_value"] = spacing_value

            if "range_percent" in data:
                range_percent = Decimal(str(data["range_percent"]))
                if range_percent <= 0:
                    return web.json_response(
                        {"error": "range_percent must be positive"},
                        status=400,
                    )
                kwargs["range_percent"] = range_percent

            if "max_total_orders" in data:
                max_total_orders = int(data["max_total_orders"])
                if max_total_orders <= 0:
                    return web.json_response(
                        {"error": "max_total_orders must be positive"},
                        status=400,
                    )
                kwargs["max_total_orders"] = max_total_orders

            if "anchor_mode" in data:
                anchor_mode = str(data["anchor_mode"])
                if anchor_mode not in ["none", "hundred"]:
                    return web.json_response(
                        {"error": "anchor_mode must be 'none' or 'hundred'"},
                        status=400,
                    )
                kwargs["anchor_mode"] = anchor_mode

            if "anchor_value" in data:
                anchor_value = Decimal(str(data["anchor_value"]))
                if anchor_value <= 0:
                    return web.json_response(
                        {"error": "anchor_value must be positive"},
                        status=400,
                    )
                kwargs["anchor_value"] = anchor_value

            # Update config
            config = await self._grid_config_repo.save_config(
                self._account_id,
                **kwargs,  # type: ignore[arg-type]
            )

            main_logger.info(f"Grid config updated (partial): {list(kwargs.keys())}")

            return web.json_response(
                {
                    "message": "Grid configuration updated successfully",
                    "updated_fields": list(kwargs.keys()),
                    "config": self._grid_config_repo.to_dict(config),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    # Multi-account handlers (with account_id from path)

    async def _handle_get_trading_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle GET /api/accounts/{account_id}/configs/trading request.

        Returns current trading configuration for the specified account.
        """
        main_logger.debug(
            f"GET /api/accounts/{{account_id}}/configs/trading request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._trading_config_repo:
                return web.json_response(
                    {"error": "Trading config repository not configured"},
                    status=500,
                )

            # Get current config
            config = await self._trading_config_repo.get_by_account(account_id)

            if not config:
                return web.json_response(
                    {"error": "No trading configuration found for this account"},
                    status=404,
                )

            # Convert to dict for JSON response
            return web.json_response(
                {
                    "id": str(config.id),
                    "account_id": str(config.account_id),
                    "symbol": config.symbol,
                    "leverage": config.leverage,
                    "order_size_usdt": float(config.order_size_usdt),
                    "margin_mode": config.margin_mode,
                    "take_profit_percent": float(config.take_profit_percent),
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat(),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error getting trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_put_trading_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle PUT /api/accounts/{account_id}/configs/trading request.

        Updates all trading configuration fields for the specified account.
        """
        main_logger.debug(
            f"PUT /api/accounts/{{account_id}}/configs/trading request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._trading_config_repo:
                return web.json_response(
                    {"error": "Trading config repository not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            # Validate required fields
            required_fields = [
                "symbol",
                "leverage",
                "order_size_usdt",
                "margin_mode",
                "take_profit_percent",
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                return web.json_response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=400,
                )

            # Validate field types and values
            try:
                symbol = str(data["symbol"])
                leverage = int(data["leverage"])
                order_size_usdt = Decimal(str(data["order_size_usdt"]))
                margin_mode = str(data["margin_mode"])
                take_profit_percent = Decimal(str(data["take_profit_percent"]))

                # Validate ranges
                if leverage < 1 or leverage > 125:
                    return web.json_response(
                        {"error": "Leverage must be between 1 and 125"},
                        status=400,
                    )

                if order_size_usdt <= 0:
                    return web.json_response(
                        {"error": "Order size must be positive"},
                        status=400,
                    )

                if margin_mode not in ["CROSSED", "ISOLATED"]:
                    return web.json_response(
                        {"error": "Margin mode must be CROSSED or ISOLATED"},
                        status=400,
                    )

                if take_profit_percent <= 0 or take_profit_percent > 10:
                    return web.json_response(
                        {"error": "Take profit percent must be between 0 and 10"},
                        status=400,
                    )

            except (ValueError, TypeError) as e:
                return web.json_response(
                    {"error": f"Invalid field value: {e}"},
                    status=400,
                )

            # Update config
            config = await self._trading_config_repo.create_or_update(
                account_id,
                symbol=symbol,
                leverage=leverage,
                order_size_usdt=order_size_usdt,
                margin_mode=margin_mode,
                take_profit_percent=take_profit_percent,
            )

            main_logger.info(f"Trading config updated for account {account_id}: {config}")

            return web.json_response(
                {
                    "message": "Trading configuration updated successfully",
                    "config": {
                        "id": str(config.id),
                        "account_id": str(config.account_id),
                        "symbol": config.symbol,
                        "leverage": config.leverage,
                        "order_size_usdt": float(config.order_size_usdt),
                        "margin_mode": config.margin_mode,
                        "take_profit_percent": float(config.take_profit_percent),
                        "updated_at": config.updated_at.isoformat(),
                    },
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_patch_trading_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle PATCH /api/accounts/{account_id}/configs/trading request.

        Updates specific trading configuration fields for the specified account.
        """
        main_logger.debug(
            f"PATCH /api/accounts/{{account_id}}/configs/trading request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._trading_config_repo:
                return web.json_response(
                    {"error": "Trading config repository not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            if not data:
                return web.json_response(
                    {"error": "No fields provided to update"},
                    status=400,
                )

            # Build kwargs with validated values
            kwargs: dict[str, str | int | Decimal] = {}

            if "symbol" in data:
                kwargs["symbol"] = str(data["symbol"])

            if "leverage" in data:
                leverage = int(data["leverage"])
                if leverage < 1 or leverage > 125:
                    return web.json_response(
                        {"error": "Leverage must be between 1 and 125"},
                        status=400,
                    )
                kwargs["leverage"] = leverage

            if "order_size_usdt" in data:
                order_size = Decimal(str(data["order_size_usdt"]))
                if order_size <= 0:
                    return web.json_response(
                        {"error": "Order size must be positive"},
                        status=400,
                    )
                kwargs["order_size_usdt"] = order_size

            if "margin_mode" in data:
                margin_mode = str(data["margin_mode"])
                if margin_mode not in ["CROSSED", "ISOLATED"]:
                    return web.json_response(
                        {"error": "Margin mode must be CROSSED or ISOLATED"},
                        status=400,
                    )
                kwargs["margin_mode"] = margin_mode

            if "take_profit_percent" in data:
                tp_percent = Decimal(str(data["take_profit_percent"]))
                if tp_percent <= 0 or tp_percent > 10:
                    return web.json_response(
                        {"error": "Take profit percent must be between 0 and 10"},
                        status=400,
                    )
                kwargs["take_profit_percent"] = tp_percent

            # Update config
            config = await self._trading_config_repo.create_or_update(
                account_id,
                **kwargs,  # type: ignore[arg-type]
            )

            main_logger.info(
                f"Trading config updated (partial) for account {account_id}: {list(kwargs.keys())}"
            )

            return web.json_response(
                {
                    "message": "Trading configuration updated successfully",
                    "updated_fields": list(kwargs.keys()),
                    "config": {
                        "id": str(config.id),
                        "account_id": str(config.account_id),
                        "symbol": config.symbol,
                        "leverage": config.leverage,
                        "order_size_usdt": float(config.order_size_usdt),
                        "margin_mode": config.margin_mode,
                        "take_profit_percent": float(config.take_profit_percent),
                        "updated_at": config.updated_at.isoformat(),
                    },
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating trading config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_get_grid_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle GET /api/accounts/{account_id}/configs/grid request.

        Returns current grid configuration for the specified account.
        """
        main_logger.debug(
            f"GET /api/accounts/{{account_id}}/configs/grid request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._grid_config_repo:
                return web.json_response(
                    {"error": "Grid config repository not configured"},
                    status=500,
                )

            # Get current config (or create with defaults if doesn't exist)
            config = await self._grid_config_repo.get_or_create(account_id)

            # Convert to dict for JSON response
            return web.json_response(
                self._grid_config_repo.to_dict(config),
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error getting grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_put_grid_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle PUT /api/accounts/{account_id}/configs/grid request.

        Updates all grid configuration fields for the specified account.
        """
        main_logger.debug(
            f"PUT /api/accounts/{{account_id}}/configs/grid request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._grid_config_repo:
                return web.json_response(
                    {"error": "Grid config repository not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            # Validate required fields
            required_fields = [
                "spacing_type",
                "spacing_value",
                "range_percent",
                "max_total_orders",
                "anchor_mode",
                "anchor_value",
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                return web.json_response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=400,
                )

            # Validate field types and values
            try:
                spacing_type = str(data["spacing_type"])
                spacing_value = Decimal(str(data["spacing_value"]))
                range_percent = Decimal(str(data["range_percent"]))
                max_total_orders = int(data["max_total_orders"])
                anchor_mode = str(data["anchor_mode"])
                anchor_value = Decimal(str(data["anchor_value"]))

                # Validate spacing_type
                if spacing_type not in ["fixed", "percentage"]:
                    return web.json_response(
                        {"error": "spacing_type must be 'fixed' or 'percentage'"},
                        status=400,
                    )

                # Validate positive values
                if spacing_value <= 0:
                    return web.json_response(
                        {"error": "spacing_value must be positive"},
                        status=400,
                    )

                if range_percent <= 0:
                    return web.json_response(
                        {"error": "range_percent must be positive"},
                        status=400,
                    )

                if max_total_orders <= 0:
                    return web.json_response(
                        {"error": "max_total_orders must be positive"},
                        status=400,
                    )

                # Validate anchor_mode
                if anchor_mode not in ["none", "hundred"]:
                    return web.json_response(
                        {"error": "anchor_mode must be 'none' or 'hundred'"},
                        status=400,
                    )

                if anchor_value <= 0:
                    return web.json_response(
                        {"error": "anchor_value must be positive"},
                        status=400,
                    )

            except (ValueError, TypeError) as e:
                return web.json_response(
                    {"error": f"Invalid field value: {e}"},
                    status=400,
                )

            # Update config
            config = await self._grid_config_repo.save_config(
                account_id,
                spacing_type=spacing_type,
                spacing_value=spacing_value,
                range_percent=range_percent,
                max_total_orders=max_total_orders,
                anchor_mode=anchor_mode,
                anchor_value=anchor_value,
            )

            main_logger.info(f"Grid config updated for account {account_id}: {config}")

            return web.json_response(
                {
                    "message": "Grid configuration updated successfully",
                    "config": self._grid_config_repo.to_dict(config),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    async def _handle_patch_grid_config_multi(self, request: web.Request) -> web.Response:
        """
        Handle PATCH /api/accounts/{account_id}/configs/grid request.

        Updates specific grid configuration fields for the specified account.
        """
        main_logger.debug(
            f"PATCH /api/accounts/{{account_id}}/configs/grid request from {request.remote}"
        )

        try:
            # Extract and validate account_id from path
            try:
                account_id = UUID(request.match_info["account_id"])
            except (KeyError, ValueError):
                return web.json_response(
                    {"error": "Invalid account_id in URL path"},
                    status=400,
                )

            if not self._grid_config_repo:
                return web.json_response(
                    {"error": "Grid config repository not configured"},
                    status=500,
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400,
                )

            if not data:
                return web.json_response(
                    {"error": "No fields provided to update"},
                    status=400,
                )

            # Build kwargs with validated values
            kwargs: dict[str, str | int | Decimal] = {}

            if "spacing_type" in data:
                spacing_type = str(data["spacing_type"])
                if spacing_type not in ["fixed", "percentage"]:
                    return web.json_response(
                        {"error": "spacing_type must be 'fixed' or 'percentage'"},
                        status=400,
                    )
                kwargs["spacing_type"] = spacing_type

            if "spacing_value" in data:
                spacing_value = Decimal(str(data["spacing_value"]))
                if spacing_value <= 0:
                    return web.json_response(
                        {"error": "spacing_value must be positive"},
                        status=400,
                    )
                kwargs["spacing_value"] = spacing_value

            if "range_percent" in data:
                range_percent = Decimal(str(data["range_percent"]))
                if range_percent <= 0:
                    return web.json_response(
                        {"error": "range_percent must be positive"},
                        status=400,
                    )
                kwargs["range_percent"] = range_percent

            if "max_total_orders" in data:
                max_total_orders = int(data["max_total_orders"])
                if max_total_orders <= 0:
                    return web.json_response(
                        {"error": "max_total_orders must be positive"},
                        status=400,
                    )
                kwargs["max_total_orders"] = max_total_orders

            if "anchor_mode" in data:
                anchor_mode = str(data["anchor_mode"])
                if anchor_mode not in ["none", "hundred"]:
                    return web.json_response(
                        {"error": "anchor_mode must be 'none' or 'hundred'"},
                        status=400,
                    )
                kwargs["anchor_mode"] = anchor_mode

            if "anchor_value" in data:
                anchor_value = Decimal(str(data["anchor_value"]))
                if anchor_value <= 0:
                    return web.json_response(
                        {"error": "anchor_value must be positive"},
                        status=400,
                    )
                kwargs["anchor_value"] = anchor_value

            # Update config
            config = await self._grid_config_repo.save_config(
                account_id,
                **kwargs,  # type: ignore[arg-type]
            )

            main_logger.info(
                f"Grid config updated (partial) for account {account_id}: {list(kwargs.keys())}"
            )

            return web.json_response(
                {
                    "message": "Grid configuration updated successfully",
                    "updated_fields": list(kwargs.keys()),
                    "config": self._grid_config_repo.to_dict(config),
                },
                status=200,
            )

        except Exception as e:
            main_logger.error(f"Error updating grid config: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

    @property
    def is_running(self) -> bool:
        """Check if health server is running."""
        return self._running
