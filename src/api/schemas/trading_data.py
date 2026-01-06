"""Pydantic schemas for trading data API responses."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


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
    """Schema for a completed trade."""

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
