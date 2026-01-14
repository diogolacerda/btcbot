"""Bot control endpoints for managing the trading bot."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_active_user, get_grid_manager
from src.api.schemas.bot_control import (
    BotPauseResponse,
    BotResumeResponse,
    BotStartResponse,
    BotStatusResponse,
    BotStopResponse,
    ErrorStatus,
    MACDValues,
    OrderStats,
)
from src.database.models.activity_event import EventType
from src.database.models.user import User
from src.utils.logger import main_logger

if TYPE_CHECKING:
    from src.grid.grid_manager import GridManager

router = APIRouter(prefix="/api/v1/bot", tags=["Bot Control"])

# Map GridState values to human-readable descriptions
STATE_DESCRIPTIONS = {
    "wait": "Waiting for MACD signal to activate",
    "activate": "MACD signal detected, activating grid",
    "active": "Grid is active, placing and managing orders",
    "pause": "Grid temporarily paused",
    "inactive": "Grid inactive due to bearish MACD signal",
}


def _get_state_description(state: str) -> str:
    """Get human-readable description for a grid state."""
    return STATE_DESCRIPTIONS.get(state.lower(), f"Unknown state: {state}")


def _get_bot_status_string(grid_manager: "GridManager") -> str:
    """Determine the bot status string based on GridManager state."""
    if not grid_manager.is_running:
        return "stopped"
    grid_status = grid_manager.get_status()
    if grid_status.margin_error:
        return "paused"
    return "running"


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    grid_manager: Annotated["GridManager", Depends(get_grid_manager)],
):
    """Get current bot status including state, MACD values, and order statistics.

    Returns:
        BotStatusResponse: Complete bot status information
    """
    try:
        grid_status = grid_manager.get_status()
        state_value = grid_status.state.value

        return BotStatusResponse(
            status=_get_bot_status_string(grid_manager),
            state=state_value.upper(),
            state_description=_get_state_description(state_value),
            is_running=grid_manager.is_running,
            cycle_activated=grid_status.cycle_activated,
            cycle_activated_at=None,  # TODO: Add cycle_activated_at to MACDStrategy
            last_update=datetime.now(UTC),
            current_price=grid_status.current_price,
            macd=MACDValues(
                macd_line=grid_status.macd_line,
                histogram=grid_status.histogram,
            ),
            orders=OrderStats(
                pending_orders=grid_status.pending_orders,
                open_positions=grid_status.open_positions,
                total_trades=grid_status.total_trades,
                total_pnl=grid_status.total_pnl,
            ),
            errors=ErrorStatus(
                margin_error=grid_status.margin_error,
                rate_limited=grid_status.rate_limited,
            ),
        )

    except Exception as e:
        main_logger.error(f"Error getting bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/pause", response_model=BotPauseResponse)
async def pause_bot(
    current_user: Annotated[User, Depends(get_current_active_user)],
    grid_manager: Annotated["GridManager", Depends(get_grid_manager)],
):
    """Pause the bot by setting margin_error flag.

    This prevents new orders from being created while preserving existing positions
    and TP orders.

    Returns:
        BotPauseResponse: Result of the pause operation
    """
    try:
        if not grid_manager.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not running. Cannot pause a stopped bot.",
            )

        previous_state = grid_manager.current_state.value.upper()

        # Set margin_error flag to pause order creation
        grid_manager._margin_error = True
        grid_manager._margin_error_time = datetime.now(UTC).timestamp()

        main_logger.info("Bot paused via API")

        # Log STRATEGY_PAUSED event
        grid_manager._log_activity_event(
            EventType.STRATEGY_PAUSED,
            "Bot paused via dashboard",
            {
                "previous_state": previous_state,
                "current_state": grid_manager.current_state.value.upper(),
                "pending_orders": grid_manager.tracker.pending_count,
                "open_positions": grid_manager.tracker.position_count,
            },
        )

        # Broadcast pause status to dashboard
        grid_manager._broadcast_bot_status(
            state=grid_manager.current_state,
            is_running=grid_manager.is_running,
            macd_trend=None,
            grid_active=False,
            pending_orders_count=grid_manager.tracker.pending_count,
            filled_orders_count=grid_manager.tracker.position_count,
            macd_line=grid_manager._last_macd_line,
            histogram=grid_manager._last_histogram,
            signal_line=None,
        )

        return BotPauseResponse(
            success=True,
            message="Bot paused successfully. No new orders will be created.",
            previous_state=previous_state,
            current_state=grid_manager.current_state.value.upper(),
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error pausing bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/resume", response_model=BotResumeResponse)
async def resume_bot(
    current_user: Annotated[User, Depends(get_current_active_user)],
    grid_manager: Annotated["GridManager", Depends(get_grid_manager)],
):
    """Resume the bot by clearing margin_error flag.

    This allows the bot to resume creating orders.

    Returns:
        BotResumeResponse: Result of the resume operation
    """
    try:
        if not grid_manager.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not running. Use /start to start the bot.",
            )

        previous_state = grid_manager.current_state.value.upper()

        # Clear margin_error flag to resume order creation
        grid_manager._margin_error = False
        grid_manager._margin_error_time = 0.0

        main_logger.info("Bot resumed via API")

        # Log STRATEGY_RESUMED event
        grid_manager._log_activity_event(
            EventType.STRATEGY_RESUMED,
            "Bot resumed via dashboard",
            {
                "previous_state": previous_state,
                "current_state": grid_manager.current_state.value.upper(),
                "pending_orders": grid_manager.tracker.pending_count,
                "open_positions": grid_manager.tracker.position_count,
            },
        )

        # Broadcast resume status to dashboard
        grid_manager._broadcast_bot_status(
            state=grid_manager.current_state,
            is_running=grid_manager.is_running,
            macd_trend=None,
            grid_active=grid_manager.current_state.value in ("ACTIVATE", "ACTIVE"),
            pending_orders_count=grid_manager.tracker.pending_count,
            filled_orders_count=grid_manager.tracker.position_count,
            macd_line=grid_manager._last_macd_line,
            histogram=grid_manager._last_histogram,
            signal_line=None,
        )

        return BotResumeResponse(
            success=True,
            message="Bot resumed successfully. Order creation is now enabled.",
            previous_state=previous_state,
            current_state=grid_manager.current_state.value.upper(),
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error resuming bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/stop", response_model=BotStopResponse)
async def stop_bot(
    current_user: Annotated[User, Depends(get_current_active_user)],
    grid_manager: Annotated["GridManager", Depends(get_grid_manager)],
):
    """Stop the bot and cancel pending LIMIT orders.

    This stops the bot's main loop, cancels all pending LIMIT orders,
    but preserves TP/SL orders for existing positions.

    Returns:
        BotStopResponse: Result of the stop operation including order counts
    """
    try:
        if not grid_manager.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already stopped.",
            )

        # Get current order counts before stopping
        grid_status = grid_manager.get_status()
        pending_before = grid_status.pending_orders

        # Stop the grid manager (cancels LIMIT orders, preserves TPs)
        grid_manager.stop()

        main_logger.info("Bot stopped via API")

        return BotStopResponse(
            success=True,
            message="Bot stopped successfully. LIMIT orders cancelled, TP/SL orders preserved.",
            orders_cancelled=pending_before,
            tp_orders_preserved=grid_status.open_positions,
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error stopping bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/start", response_model=BotStartResponse)
async def start_bot(
    current_user: Annotated[User, Depends(get_current_active_user)],
    grid_manager: Annotated["GridManager", Depends(get_grid_manager)],
):
    """Start the bot.

    This starts the bot's main loop if it's not already running.

    Returns:
        BotStartResponse: Result of the start operation
    """
    try:
        if grid_manager.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running.",
            )

        # Start the grid manager
        grid_manager.start()

        main_logger.info("Bot started via API")

        return BotStartResponse(
            success=True,
            message="Bot started successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error starting bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
