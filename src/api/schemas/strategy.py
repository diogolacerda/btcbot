"""Schemas for Strategy API endpoints and MACD filter configuration."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class StrategyCreate(BaseModel):
    """Schema for creating a new strategy (POST)."""

    name: str = Field(min_length=1, max_length=100, description="Strategy name")
    is_active: bool = Field(default=False, description="Whether this strategy is active")
    symbol: str = Field(default="BTC-USDT", description="Trading pair symbol")

    # Risk parameters
    leverage: int = Field(default=10, ge=1, le=125, description="Leverage multiplier (1-125x)")
    order_size_usdt: Decimal = Field(
        default=Decimal("100.00"), gt=0, description="Order size in USDT"
    )
    margin_mode: str = Field(default="crossed", description="Margin mode (crossed or isolated)")

    # Take profit parameters
    take_profit_percent: Decimal = Field(
        default=Decimal("0.50"), gt=0, le=10, description="Take profit percentage (0-10%)"
    )

    # Dynamic TP parameters
    tp_dynamic_enabled: bool = Field(
        default=False, description="Enable dynamic TP based on funding rate"
    )
    tp_dynamic_base: Decimal = Field(
        default=Decimal("0.30"), gt=0, description="Base TP percentage for dynamic calculation"
    )
    tp_dynamic_min: Decimal = Field(
        default=Decimal("0.30"), gt=0, description="Minimum TP percentage"
    )
    tp_dynamic_max: Decimal = Field(
        default=Decimal("1.00"), gt=0, description="Maximum TP percentage"
    )
    tp_dynamic_safety_margin: Decimal = Field(
        default=Decimal("0.05"), ge=0, description="Safety margin above funding cost"
    )
    tp_dynamic_check_interval: int = Field(
        default=60, gt=0, description="Check interval in minutes"
    )

    # Grid parameters
    spacing_type: str = Field(
        default="fixed", description="Grid spacing type (fixed or percentage)"
    )
    spacing_value: Decimal = Field(default=Decimal("100.0"), gt=0, description="Grid spacing value")
    range_percent: Decimal = Field(
        default=Decimal("5.0"), gt=0, description="Grid range as percentage from current price"
    )
    max_total_orders: int = Field(default=10, gt=0, description="Maximum total orders")

    @field_validator("margin_mode")
    @classmethod
    def validate_margin_mode(cls, v: str) -> str:
        """Validate margin mode is either crossed or isolated."""
        v_lower = v.lower()
        if v_lower not in ["crossed", "isolated"]:
            raise ValueError("Margin mode must be 'crossed' or 'isolated'")
        return v_lower

    @field_validator("spacing_type")
    @classmethod
    def validate_spacing_type(cls, v: str) -> str:
        """Validate spacing type is either fixed or percentage."""
        v_lower = v.lower()
        if v_lower not in ["fixed", "percentage"]:
            raise ValueError("spacing_type must be 'fixed' or 'percentage'")
        return v_lower


class StrategyUpdate(BaseModel):
    """Schema for partial strategy updates (PATCH)."""

    name: str | None = Field(
        default=None, min_length=1, max_length=100, description="Strategy name"
    )
    is_active: bool | None = Field(default=None, description="Whether this strategy is active")
    symbol: str | None = Field(default=None, description="Trading pair symbol")

    # Risk parameters
    leverage: int | None = Field(default=None, ge=1, le=125, description="Leverage multiplier")
    order_size_usdt: Decimal | None = Field(default=None, gt=0, description="Order size in USDT")
    margin_mode: str | None = Field(default=None, description="Margin mode")

    # Take profit parameters
    take_profit_percent: Decimal | None = Field(
        default=None, gt=0, le=10, description="Take profit percentage"
    )

    # Dynamic TP parameters
    tp_dynamic_enabled: bool | None = Field(default=None, description="Enable dynamic TP")
    tp_dynamic_base: Decimal | None = Field(default=None, gt=0, description="Base TP percentage")
    tp_dynamic_min: Decimal | None = Field(default=None, gt=0, description="Minimum TP percentage")
    tp_dynamic_max: Decimal | None = Field(default=None, gt=0, description="Maximum TP percentage")
    tp_dynamic_safety_margin: Decimal | None = Field(
        default=None, ge=0, description="Safety margin"
    )
    tp_dynamic_check_interval: int | None = Field(default=None, gt=0, description="Check interval")

    # Grid parameters
    spacing_type: str | None = Field(default=None, description="Grid spacing type")
    spacing_value: Decimal | None = Field(default=None, gt=0, description="Grid spacing value")
    range_percent: Decimal | None = Field(default=None, gt=0, description="Grid range percentage")
    max_total_orders: int | None = Field(default=None, gt=0, description="Maximum total orders")

    @field_validator("margin_mode")
    @classmethod
    def validate_margin_mode(cls, v: str | None) -> str | None:
        """Validate margin mode is either crossed or isolated."""
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["crossed", "isolated"]:
                raise ValueError("Margin mode must be 'crossed' or 'isolated'")
            return v_lower
        return v

    @field_validator("spacing_type")
    @classmethod
    def validate_spacing_type(cls, v: str | None) -> str | None:
        """Validate spacing type is either fixed or percentage."""
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["fixed", "percentage"]:
                raise ValueError("spacing_type must be 'fixed' or 'percentage'")
            return v_lower
        return v


class StrategyResponse(BaseModel):
    """Response schema for strategy."""

    id: str
    account_id: str
    name: str
    is_active: bool
    symbol: str

    # Risk parameters
    leverage: int
    order_size_usdt: Decimal
    margin_mode: str

    # Take profit parameters
    take_profit_percent: Decimal

    # Dynamic TP parameters
    tp_dynamic_enabled: bool
    tp_dynamic_base: Decimal
    tp_dynamic_min: Decimal
    tp_dynamic_max: Decimal
    tp_dynamic_safety_margin: Decimal
    tp_dynamic_check_interval: int

    # Grid parameters
    spacing_type: str
    spacing_value: Decimal
    range_percent: Decimal
    max_total_orders: int

    # Timestamps
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "order_size_usdt",
        "take_profit_percent",
        "tp_dynamic_base",
        "tp_dynamic_min",
        "tp_dynamic_max",
        "tp_dynamic_safety_margin",
        "spacing_value",
        "range_percent",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        """Normalize Decimal values to remove trailing zeros.

        Example: Decimal("0.60") -> "0.6", Decimal("100.00") -> "100"
        This ensures consistent formatting in API responses without scientific notation.
        """
        result = str(value)
        if "." in result:
            result = result.rstrip("0").rstrip(".")
        return result

    model_config = ConfigDict(from_attributes=True)


class StrategyActivateResponse(BaseModel):
    """Response schema for strategy activation."""

    message: str
    strategy: StrategyResponse


# MACD Filter Config Schemas


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


# EMA Filter Config Schemas


class EMAFilterConfigUpdate(BaseModel):
    """Schema for partial EMA filter configuration updates (PATCH).

    The EMA filter is part of the Impulse System (Alexander Elder).
    When EMA is rising, it indicates bullish trend (allow trades).
    When EMA is falling, it indicates bearish trend (protect orders).
    """

    enabled: bool | None = Field(default=None, description="Whether the EMA filter is enabled")
    period: int | None = Field(default=None, gt=0, description="EMA period (default 13)")
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"] | None = Field(
        default=None, description="Candle timeframe for EMA calculation"
    )
    allow_on_rising: bool | None = Field(
        default=None, description="Allow new orders when EMA is rising (bullish)"
    )
    allow_on_falling: bool | None = Field(
        default=None, description="Allow new orders when EMA is falling (bearish)"
    )


class EMAFilterConfigResponse(BaseModel):
    """Response schema for EMA filter configuration."""

    id: str
    strategy_id: str
    enabled: bool
    period: int
    timeframe: str
    allow_on_rising: bool
    allow_on_falling: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
