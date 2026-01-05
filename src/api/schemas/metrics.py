"""Pydantic schemas for performance metrics API."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TimePeriod(str, Enum):
    """Time period options for filtering metrics."""

    TODAY = "today"
    SEVEN_DAYS = "7days"
    THIRTY_DAYS = "30days"
    CUSTOM = "custom"


class PeriodMetrics(BaseModel):
    """Metrics for a specific time period."""

    period: str = Field(..., description="Period description (e.g., 'today', '7days')")
    start_date: datetime = Field(..., description="Start of the period")
    end_date: datetime = Field(..., description="End of the period")
    realized_pnl: Decimal = Field(..., description="Realized P&L in the period")
    pnl_percent: Decimal = Field(..., description="P&L percentage relative to trades volume")
    trades_closed: int = Field(..., description="Number of trades closed in the period")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: Decimal = Field(..., description="Win rate percentage")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "today",
                "start_date": "2026-01-05T00:00:00Z",
                "end_date": "2026-01-05T23:59:59Z",
                "realized_pnl": "25.50",
                "pnl_percent": "1.25",
                "trades_closed": 12,
                "winning_trades": 8,
                "losing_trades": 4,
                "win_rate": "66.67",
            }
        },
    }


class TotalMetrics(BaseModel):
    """Cumulative metrics for all time."""

    total_pnl: Decimal = Field(..., description="Total realized P&L all time")
    total_trades: int = Field(..., description="Total number of closed trades")
    avg_profit_per_trade: Decimal = Field(..., description="Average profit per trade")
    total_fees: Decimal = Field(..., description="Total fees paid")
    net_pnl: Decimal = Field(..., description="Net P&L (total_pnl - total_fees)")
    best_trade: Decimal = Field(..., description="Best single trade P&L")
    worst_trade: Decimal = Field(..., description="Worst single trade P&L")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_pnl": "1250.75",
                "total_trades": 450,
                "avg_profit_per_trade": "2.78",
                "total_fees": "85.50",
                "net_pnl": "1165.25",
                "best_trade": "45.00",
                "worst_trade": "-22.50",
            }
        },
    }


class PerformanceMetricsResponse(BaseModel):
    """Response schema for GET /api/v1/metrics/performance."""

    period_metrics: PeriodMetrics = Field(..., description="Metrics for the selected time period")
    total_metrics: TotalMetrics = Field(..., description="Cumulative metrics for all time")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period_metrics": {
                    "period": "7days",
                    "start_date": "2025-12-29T00:00:00Z",
                    "end_date": "2026-01-05T23:59:59Z",
                    "realized_pnl": "85.25",
                    "pnl_percent": "2.15",
                    "trades_closed": 42,
                    "winning_trades": 28,
                    "losing_trades": 14,
                    "win_rate": "66.67",
                },
                "total_metrics": {
                    "total_pnl": "1250.75",
                    "total_trades": 450,
                    "avg_profit_per_trade": "2.78",
                    "total_fees": "85.50",
                    "net_pnl": "1165.25",
                    "best_trade": "45.00",
                    "worst_trade": "-22.50",
                },
            }
        },
    }
