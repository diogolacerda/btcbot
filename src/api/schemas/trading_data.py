"""Pydantic schemas for trading data API responses."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TpAdjustmentSchema(BaseModel):
    """Schema for a Take Profit adjustment record.

    Represents a single TP adjustment made by the Dynamic TP Manager,
    showing when and why the take profit target was changed.
    """

    timestamp: datetime = Field(..., description="When the adjustment was made")
    old_tp: Decimal = Field(..., description="Previous TP percentage")
    new_tp: Decimal = Field(..., description="New TP percentage")
    reason: str = Field(..., description="Reason for adjustment (funding rate impact)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-01-03T18:30:00Z",
                "old_tp": "0.5",
                "new_tp": "0.6",
                "reason": "Funding rate: 0.01%, accumulated: 0.5%, 8.5h open",
            }
        },
    }


class TradeFeesSchema(BaseModel):
    """Schema for trade fee breakdown and net P&L.

    Provides a detailed view of fees and the true profit after all costs.
    """

    trading_fee: Decimal = Field(..., description="Trading fees paid")
    funding_fee: Decimal = Field(..., description="Funding fees paid/received")
    net_pnl: Decimal = Field(
        ..., description="Net P&L after all fees (pnl - trading_fee - funding_fee)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "trading_fee": "0.05",
                "funding_fee": "0.01",
                "net_pnl": "0.44",
            }
        },
    }


class PositionSchema(BaseModel):
    """Schema for an open position."""

    symbol: str = Field(..., description="Trading symbol (e.g., BTC-USDT)")
    side: str = Field(..., description="Position side (LONG or SHORT)")
    leverage: int = Field(..., description="Leverage used")
    entry_price: Decimal = Field(..., description="Entry price")
    quantity: Decimal = Field(..., description="Position size")
    tp_price: Decimal | None = Field(None, description="Take profit price")
    tp_percent: Decimal | None = Field(None, description="Take profit percentage")
    unrealized_pnl: Decimal | None = Field(None, description="Unrealized P&L")
    opened_at: datetime = Field(..., description="Position opening timestamp")
    grid_level: int | None = Field(None, description="Grid level")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "BTC-USDT",
                "side": "LONG",
                "leverage": 10,
                "entry_price": "95000.00",
                "quantity": "0.001",
                "tp_price": "95500.00",
                "tp_percent": "0.5",
                "unrealized_pnl": "0.50",
                "opened_at": "2026-01-03T18:00:00Z",
                "grid_level": 1,
            }
        },
    }


class TradeSchema(BaseModel):
    """Schema for a completed trade with TP adjustment history and fees breakdown."""

    id: UUID = Field(..., description="Trade UUID")
    account_id: UUID = Field(..., description="Account UUID")
    exchange_order_id: str | None = Field(None, description="Exchange order ID")
    exchange_tp_order_id: str | None = Field(None, description="Exchange take-profit order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Trade side (LONG or SHORT)")
    leverage: int = Field(..., description="Leverage used")
    entry_price: Decimal = Field(..., description="Entry price")
    exit_price: Decimal | None = Field(None, description="Exit price")
    quantity: Decimal = Field(..., description="Trade quantity")
    tp_price: Decimal | None = Field(None, description="Take profit price")
    tp_percent: Decimal | None = Field(None, description="Take profit percentage")
    pnl: Decimal | None = Field(None, description="Profit and loss")
    pnl_percent: Decimal | None = Field(None, description="P&L percentage")
    trading_fee: Decimal = Field(..., description="Trading fees")
    funding_fee: Decimal = Field(..., description="Funding fees")
    status: str = Field(..., description="Trade status (OPEN, CLOSED, CANCELLED)")
    grid_level: int | None = Field(None, description="Grid level")
    opened_at: datetime = Field(..., description="Opening timestamp")
    filled_at: datetime | None = Field(None, description="Fill timestamp")
    closed_at: datetime | None = Field(None, description="Closing timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # New fields for BE-TRADE-003
    duration: int | None = Field(
        None,
        description="Trade duration in seconds (null for open trades)",
    )
    fees: TradeFeesSchema | None = Field(
        None,
        description="Fee breakdown with net P&L calculation",
    )
    tp_adjustments: list[TpAdjustmentSchema] = Field(
        default_factory=list,
        description="History of TP adjustments made by Dynamic TP Manager",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
                "symbol": "BTC-USDT",
                "side": "LONG",
                "leverage": 10,
                "entry_price": "95000.00",
                "exit_price": "95500.00",
                "quantity": "0.001",
                "tp_price": "95500.00",
                "tp_percent": "0.5",
                "pnl": "0.50",
                "pnl_percent": "0.53",
                "trading_fee": "0.05",
                "funding_fee": "0.01",
                "status": "CLOSED",
                "grid_level": 1,
                "opened_at": "2026-01-03T18:00:00Z",
                "filled_at": "2026-01-03T18:00:01Z",
                "closed_at": "2026-01-03T18:05:00Z",
                "created_at": "2026-01-03T18:00:00Z",
                "updated_at": "2026-01-03T18:05:00Z",
                "duration": 300,
                "fees": {
                    "trading_fee": "0.05",
                    "funding_fee": "0.01",
                    "net_pnl": "0.44",
                },
                "tp_adjustments": [
                    {
                        "timestamp": "2026-01-03T18:02:00Z",
                        "old_tp": "0.5",
                        "new_tp": "0.55",
                        "reason": "Funding rate: 0.01%, accumulated: 0.2%, 2h open",
                    }
                ],
            }
        },
    }


class TradeStatsSchema(BaseModel):
    """Schema for trading statistics."""

    total_trades: int = Field(..., description="Total number of trades")
    open_trades: int = Field(..., description="Number of open trades")
    closed_trades: int = Field(..., description="Number of closed trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: Decimal = Field(..., description="Win rate percentage")
    total_pnl: Decimal = Field(..., description="Total profit and loss")
    total_fees: Decimal = Field(..., description="Total fees paid")
    net_pnl: Decimal = Field(..., description="Net P&L (total_pnl - total_fees)")
    avg_pnl_per_trade: Decimal = Field(..., description="Average P&L per trade")
    avg_win: Decimal = Field(..., description="Average winning trade P&L")
    avg_loss: Decimal = Field(..., description="Average losing trade P&L")
    largest_win: Decimal = Field(..., description="Largest winning trade P&L")
    largest_loss: Decimal = Field(..., description="Largest losing trade P&L")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_trades": 100,
                "open_trades": 5,
                "closed_trades": 95,
                "winning_trades": 60,
                "losing_trades": 35,
                "win_rate": "63.16",
                "total_pnl": "150.75",
                "total_fees": "10.50",
                "net_pnl": "140.25",
                "avg_pnl_per_trade": "1.51",
                "avg_win": "3.50",
                "avg_loss": "-2.00",
                "largest_win": "15.00",
                "largest_loss": "-8.50",
            }
        },
    }


class PositionsListResponse(BaseModel):
    """Response schema for list of positions."""

    positions: list[PositionSchema] = Field(..., description="List of open positions")
    total: int = Field(..., description="Total number of positions")


class TradesListResponse(BaseModel):
    """Response schema for list of trades."""

    trades: list[TradeSchema] = Field(..., description="List of trades")
    total: int = Field(..., description="Total number of trades")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")


class BestWorstTradeSchema(BaseModel):
    """Schema for best or worst trade details."""

    id: UUID | None = Field(None, description="Trade UUID (null if no trades)")
    pnl: Decimal = Field(..., description="Profit and loss")
    date: datetime | None = Field(None, description="Trade close date (null if no trades)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "pnl": "15.50",
                "date": "2026-01-05T14:30:00Z",
            }
        },
    }


class CumulativePnlDataPointSchema(BaseModel):
    """Schema for a single data point in the cumulative P&L chart.

    Represents one day's cumulative P&L value, used to plot the equity curve.
    """

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    cumulative_pnl: Decimal = Field(..., description="Running total P&L up to this date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-01-05",
                "cumulative_pnl": "250.75",
            }
        },
    }


class CumulativePnlResponse(BaseModel):
    """Response schema for cumulative P&L chart endpoint.

    Returns daily data points for plotting an equity curve chart.
    Each point contains the running total P&L up to that date.
    """

    data: list[CumulativePnlDataPointSchema] = Field(
        ..., description="List of daily cumulative P&L data points"
    )
    period: str = Field(..., description="Period filter applied (today, 7days, 30days, custom)")
    period_start: datetime | None = Field(None, description="Period start date")
    period_end: datetime | None = Field(None, description="Period end date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"date": "2026-01-01", "cumulative_pnl": "50.25"},
                    {"date": "2026-01-02", "cumulative_pnl": "125.50"},
                    {"date": "2026-01-03", "cumulative_pnl": "100.75"},
                    {"date": "2026-01-04", "cumulative_pnl": "175.00"},
                    {"date": "2026-01-05", "cumulative_pnl": "250.75"},
                ],
                "period": "7days",
                "period_start": "2025-12-30T00:00:00Z",
                "period_end": "2026-01-05T23:59:59Z",
            }
        },
    }


class PerformanceMetricsSchema(BaseModel):
    """Schema for performance metrics endpoint response.

    Includes comprehensive trading analytics with ROI based on capital employed.
    """

    total_pnl: Decimal = Field(..., description="Sum of all P&L (USDT)")
    roi: Decimal = Field(
        ..., description="Return on Investment: (totalPnl / capital_employed) * 100"
    )
    total_trades: int = Field(..., description="Total number of closed trades")
    winning_trades: int = Field(..., description="Number of trades with positive P&L")
    losing_trades: int = Field(..., description="Number of trades with negative P&L")
    win_rate: Decimal = Field(..., description="Win rate percentage: (winning / total) * 100")
    avg_profit: Decimal = Field(..., description="Average profit per trade: totalPnl / totalTrades")
    best_trade: BestWorstTradeSchema = Field(..., description="Trade with highest P&L")
    worst_trade: BestWorstTradeSchema = Field(..., description="Trade with lowest P&L")
    period_start: datetime | None = Field(None, description="Period start date (if filtered)")
    period_end: datetime | None = Field(None, description="Period end date (if filtered)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_pnl": "250.75",
                "roi": "2.51",
                "total_trades": 100,
                "winning_trades": 65,
                "losing_trades": 35,
                "win_rate": "65.00",
                "avg_profit": "2.51",
                "best_trade": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "pnl": "25.50",
                    "date": "2026-01-05T14:30:00Z",
                },
                "worst_trade": {
                    "id": "456e7890-e89b-12d3-a456-426614174001",
                    "pnl": "-12.25",
                    "date": "2026-01-04T09:15:00Z",
                },
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-01-05T23:59:59Z",
            }
        },
    }
