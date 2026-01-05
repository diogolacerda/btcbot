"""Pydantic schemas for market data API responses."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class MACDSignal(str, Enum):
    """MACD signal direction."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PriceResponse(BaseModel):
    """Response schema for current BTC price."""

    symbol: str = Field(..., description="Trading symbol (e.g., BTC-USDT)")
    price: Decimal = Field(..., description="Current price")
    change_24h: Decimal = Field(..., description="24-hour price change")
    change_24h_percent: Decimal = Field(..., description="24-hour price change percentage")
    high_24h: Decimal = Field(..., description="24-hour high price")
    low_24h: Decimal = Field(..., description="24-hour low price")
    volume_24h: Decimal = Field(..., description="24-hour trading volume")
    timestamp: datetime = Field(..., description="Data timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC-USDT",
                "price": "98500.50",
                "change_24h": "1250.00",
                "change_24h_percent": "1.28",
                "high_24h": "99000.00",
                "low_24h": "97000.00",
                "volume_24h": "1234567.89",
                "timestamp": "2026-01-05T12:00:00Z",
            }
        },
    }


class FundingRateResponse(BaseModel):
    """Response schema for funding rate data."""

    symbol: str = Field(..., description="Trading symbol")
    funding_rate: Decimal = Field(..., description="Current funding rate (e.g., 0.0001 = 0.01%)")
    funding_rate_percent: Decimal = Field(..., description="Funding rate as percentage")
    next_funding_time: datetime = Field(..., description="Next funding settlement time")
    funding_interval_hours: int = Field(..., description="Funding interval in hours")
    mark_price: Decimal = Field(..., description="Current mark price")
    timestamp: datetime = Field(..., description="Data timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC-USDT",
                "funding_rate": "0.0001",
                "funding_rate_percent": "0.01",
                "next_funding_time": "2026-01-05T16:00:00Z",
                "funding_interval_hours": 8,
                "mark_price": "98500.00",
                "timestamp": "2026-01-05T12:00:00Z",
            }
        },
    }


class MACDResponse(BaseModel):
    """Response schema for MACD indicator data."""

    symbol: str = Field(..., description="Trading symbol")
    macd_line: Decimal = Field(..., description="MACD line value")
    signal_line: Decimal = Field(..., description="Signal line value")
    histogram: Decimal = Field(..., description="MACD histogram value")
    signal: MACDSignal = Field(..., description="Overall signal (bullish/bearish/neutral)")
    histogram_rising: bool = Field(..., description="Whether histogram is rising")
    both_lines_negative: bool = Field(..., description="Whether both MACD and Signal lines are < 0")
    timeframe: str = Field(..., description="Timeframe used for calculation (e.g., 1h)")
    timestamp: datetime = Field(..., description="Data timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC-USDT",
                "macd_line": "-150.25",
                "signal_line": "-180.50",
                "histogram": "30.25",
                "signal": "bullish",
                "histogram_rising": True,
                "both_lines_negative": True,
                "timeframe": "1h",
                "timestamp": "2026-01-05T12:00:00Z",
            }
        },
    }


class GridRangeResponse(BaseModel):
    """Response schema for current grid range."""

    symbol: str = Field(..., description="Trading symbol")
    current_price: Decimal = Field(..., description="Current market price")
    grid_low: Decimal = Field(..., description="Grid range lower bound")
    grid_high: Decimal = Field(..., description="Grid range upper bound (current price)")
    range_percent: Decimal = Field(..., description="Grid range percentage from config")
    price_position_percent: Decimal = Field(
        ..., description="Current price position within grid range (0-100%)"
    )
    levels_possible: int = Field(..., description="Number of grid levels possible in range")
    timestamp: datetime = Field(..., description="Data timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC-USDT",
                "current_price": "98500.00",
                "grid_low": "96530.00",
                "grid_high": "98500.00",
                "range_percent": "2.0",
                "price_position_percent": "100.0",
                "levels_possible": 10,
                "timestamp": "2026-01-05T12:00:00Z",
            }
        },
    }
