"""Schemas for strategy and MACD filter configuration endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MACDFilterConfigBase(BaseModel):
    """Base schema for MACD filter configuration."""

    enabled: bool = Field(default=True, description="Whether the MACD filter is enabled")
    fast_period: int = Field(default=12, gt=0, description="Fast EMA period for MACD calculation")
    slow_period: int = Field(default=26, gt=0, description="Slow EMA period for MACD calculation")
    signal_period: int = Field(default=9, gt=0, description="Signal line EMA period")
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"] = Field(
        default="1h", description="Candle timeframe for MACD calculation"
    )

    @field_validator("slow_period")
    @classmethod
    def validate_slow_greater_than_fast(cls, v: int, info) -> int:
        """Validate that slow period is greater than fast period."""
        if "fast_period" in info.data:
            fast_period = info.data["fast_period"]
            if v <= fast_period:
                raise ValueError("slow_period must be greater than fast_period")
        return v


class MACDFilterConfigUpdate(BaseModel):
    """Schema for partial MACD filter configuration updates (PATCH)."""

    enabled: bool | None = Field(default=None, description="Whether the MACD filter is enabled")
    fast_period: int | None = Field(default=None, gt=0, description="Fast EMA period")
    slow_period: int | None = Field(default=None, gt=0, description="Slow EMA period")
    signal_period: int | None = Field(default=None, gt=0, description="Signal line EMA period")
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"] | None = Field(
        default=None, description="Candle timeframe for MACD calculation"
    )

    @field_validator("slow_period")
    @classmethod
    def validate_slow_greater_than_fast(cls, v: int | None, info) -> int | None:
        """Validate that slow period is greater than fast period if both provided."""
        if v is not None and "fast_period" in info.data and info.data["fast_period"] is not None:
            fast_period = info.data["fast_period"]
            if v <= fast_period:
                raise ValueError("slow_period must be greater than fast_period")
        return v


class MACDFilterConfigResponse(BaseModel):
    """Response schema for MACD filter configuration."""

    id: str
    strategy_id: str
    enabled: bool
    fast_period: int
    slow_period: int
    signal_period: int
    timeframe: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
