"""Pydantic schemas for bot control endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class MACDValues(BaseModel):
    """MACD indicator values."""

    macd_line: float = Field(..., description="MACD line value")
    histogram: float = Field(..., description="MACD histogram value")


class OrderStats(BaseModel):
    """Order statistics."""

    pending_orders: int = Field(..., description="Number of pending LIMIT orders")
    open_positions: int = Field(..., description="Number of open positions")
    total_trades: int = Field(..., description="Total number of completed trades")
    total_pnl: float = Field(..., description="Total realized P&L in USDT")


class ErrorStatus(BaseModel):
    """Current error status."""

    margin_error: bool = Field(
        ...,
        description="True if paused due to insufficient margin",
    )
    rate_limited: bool = Field(
        ...,
        description="True if currently rate limited by exchange",
    )


class BotStatusResponse(BaseModel):
    """Response containing current bot status."""

    status: str = Field(
        ...,
        description="Bot running status: 'running', 'stopped', 'paused'",
    )
    state: str = Field(
        ...,
        description="Current grid state: WAIT, ACTIVATE, ACTIVE, PAUSE, INACTIVE",
    )
    state_description: str = Field(
        ...,
        description="Human-readable description of current state",
    )
    is_running: bool = Field(..., description="Whether the bot main loop is running")
    cycle_activated: bool = Field(
        ...,
        description="Whether the MACD cycle has been activated",
    )
    cycle_activated_at: datetime | None = Field(
        None,
        description="Timestamp when cycle was activated",
    )
    last_update: datetime = Field(..., description="Timestamp of last status update")
    current_price: float = Field(..., description="Current BTC price")
    macd: MACDValues = Field(..., description="Current MACD indicator values")
    orders: OrderStats = Field(..., description="Current order statistics")
    errors: ErrorStatus = Field(..., description="Current error status")


class BotPauseResponse(BaseModel):
    """Response after pausing the bot."""

    success: bool = Field(..., description="Whether pause was successful")
    message: str = Field(..., description="Result message")
    previous_state: str = Field(..., description="State before the action")
    current_state: str = Field(..., description="State after the action")


class BotResumeResponse(BaseModel):
    """Response after resuming the bot."""

    success: bool = Field(..., description="Whether resume was successful")
    message: str = Field(..., description="Result message")
    previous_state: str = Field(..., description="State before the action")
    current_state: str = Field(..., description="State after the action")


class BotStopResponse(BaseModel):
    """Response after stopping the bot."""

    success: bool = Field(..., description="Whether stop was successful")
    message: str = Field(..., description="Result message")
    orders_cancelled: int = Field(
        ...,
        description="Number of LIMIT orders cancelled",
    )
    tp_orders_preserved: int = Field(
        ...,
        description="Number of TP/SL orders preserved",
    )


class BotStartResponse(BaseModel):
    """Response after starting the bot."""

    success: bool = Field(..., description="Whether start was successful")
    message: str = Field(..., description="Result message")
