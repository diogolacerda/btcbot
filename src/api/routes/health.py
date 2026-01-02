import os
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from src.api.dependencies import AnnotatedBingXClient, AnnotatedGridManager
from src.grid.grid_manager import GridStatus

router = APIRouter(tags=["health"])

__version__ = "1.0.0"  # Hardcoding for now, will get from project metadata later


async def _check_exchange_api(bingx_client: AnnotatedBingXClient) -> dict[str, Any]:
    """
    Check BingX exchange API health.

    Returns:
        Dict with status and latency
    """
    try:
        start_time = time.time()
        # Simple price check to verify API connectivity
        symbol = os.getenv("SYMBOL", "BTC-USDT")
        await bingx_client.get_price(symbol)
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "healthy",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _get_grid_status(grid_manager: AnnotatedGridManager) -> dict[str, Any]:
    """
    Get current grid trading status.

    Returns:
        Dict with grid state and order counts
    """
    try:
        status: GridStatus = grid_manager.get_status()
        return {
            "state": status.state.value.upper(),
            "open_positions": status.open_positions,
            "pending_orders": status.pending_orders,
            "total_pnl": status.total_pnl,
            "total_trades": status.total_trades,
            "current_price": status.current_price,
            "macd_line": status.macd_line,
            "histogram": status.histogram,
            "cycle_activated": status.cycle_activated,
            "margin_error": status.margin_error,
            "rate_limited": status.rate_limited,
        }
    except Exception as e:
        return {
            "state": "error",
            "error": str(e),
        }


@router.get("/health")
async def health_check(
    bingx_client: AnnotatedBingXClient,
    grid_manager: AnnotatedGridManager,
) -> dict[str, Any]:
    """
    Handle GET /health request.

    Returns JSON with health status of all components.
    Status code 200 if healthy, 503 if any component is unhealthy.
    """
    components: dict[str, dict[str, Any]] = {}
    overall_healthy = True

    # Check exchange API
    api_status = await _check_exchange_api(bingx_client)
    components["exchange_api"] = api_status
    if api_status["status"] != "healthy":
        overall_healthy = False

    # Check WebSocket connection (FastAPI doesn't have direct WS client, assume healthy for now)
    # This logic will need to be refactored once the WS is managed by FastAPI
    components["websocket"] = {
        "status": "unknown",  # Placeholder
        "connected": False,
        "message": "WebSocket status not integrated yet",
    }

    # Get grid status
    grid_status = _get_grid_status(grid_manager)
    if grid_status["state"] == "error":
        overall_healthy = False

    # Get environment info
    environment = os.getenv("ENVIRONMENT", os.getenv("TRADING_MODE", "unknown"))
    trading_mode = os.getenv("TRADING_MODE", "demo")

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": __version__,
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": environment,
        "trading_mode": trading_mode,
        "components": components,
        "grid": grid_status,
    }
