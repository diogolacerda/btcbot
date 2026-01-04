"""Schemas for trading and grid configuration endpoints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator


class TradingConfigBase(BaseModel):
    """Base schema for trading configuration."""

    symbol: str = Field(default="BTC-USDT", description="Trading pair symbol")
    leverage: int = Field(ge=1, le=125, description="Leverage multiplier (1-125x)")
    order_size_usdt: Decimal = Field(gt=0, description="Order size in USDT")
    margin_mode: str = Field(pattern="^(CROSSED|ISOLATED)$", description="Margin mode")
    take_profit_percent: Decimal = Field(gt=0, le=10, description="Take profit percentage (0-10%)")

    # Dynamic TP fields (BE-035)
    tp_dynamic_enabled: bool = Field(
        default=False, description="Enable dynamic TP based on funding rate"
    )
    tp_base_percent: Decimal = Field(gt=0, description="Base TP percentage for dynamic TP")
    tp_min_percent: Decimal = Field(gt=0, description="Minimum TP percentage")
    tp_max_percent: Decimal = Field(gt=0, description="Maximum TP percentage")
    tp_safety_margin: Decimal = Field(ge=0, description="Safety margin above funding cost")
    tp_check_interval_min: int = Field(gt=0, description="TP check interval in minutes")

    @field_validator("margin_mode")
    @classmethod
    def validate_margin_mode(cls, v: str) -> str:
        """Validate margin mode is either CROSSED or ISOLATED."""
        if v not in ["CROSSED", "ISOLATED"]:
            raise ValueError("Margin mode must be CROSSED or ISOLATED")
        return v


class TradingConfigUpdate(BaseModel):
    """Schema for partial trading configuration updates (PATCH)."""

    symbol: str | None = Field(default=None, description="Trading pair symbol")
    leverage: int | None = Field(default=None, ge=1, le=125, description="Leverage multiplier")
    order_size_usdt: Decimal | None = Field(default=None, gt=0, description="Order size in USDT")
    margin_mode: str | None = Field(
        default=None, pattern="^(CROSSED|ISOLATED)$", description="Margin mode"
    )
    take_profit_percent: Decimal | None = Field(
        default=None, gt=0, le=10, description="Take profit percentage"
    )

    # Dynamic TP fields
    tp_dynamic_enabled: bool | None = Field(default=None, description="Enable dynamic TP")
    tp_base_percent: Decimal | None = Field(default=None, gt=0, description="Base TP percentage")
    tp_min_percent: Decimal | None = Field(default=None, gt=0, description="Minimum TP percentage")
    tp_max_percent: Decimal | None = Field(default=None, gt=0, description="Maximum TP percentage")
    tp_safety_margin: Decimal | None = Field(
        default=None, ge=0, description="Safety margin above funding cost"
    )
    tp_check_interval_min: int | None = Field(
        default=None, gt=0, description="TP check interval in minutes"
    )

    @field_validator("margin_mode")
    @classmethod
    def validate_margin_mode(cls, v: str | None) -> str | None:
        """Validate margin mode is either CROSSED or ISOLATED."""
        if v is not None and v not in ["CROSSED", "ISOLATED"]:
            raise ValueError("Margin mode must be CROSSED or ISOLATED")
        return v


class TradingConfigResponse(BaseModel):
    """Response schema for trading configuration."""

    id: str
    account_id: str
    symbol: str
    leverage: int
    order_size_usdt: Decimal
    margin_mode: str
    take_profit_percent: Decimal
    tp_dynamic_enabled: bool
    tp_base_percent: Decimal
    tp_min_percent: Decimal
    tp_max_percent: Decimal
    tp_safety_margin: Decimal
    tp_check_interval_min: int
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "order_size_usdt",
        "take_profit_percent",
        "tp_base_percent",
        "tp_min_percent",
        "tp_max_percent",
        "tp_safety_margin",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        """Normalize Decimal values to remove trailing zeros.

        Example: Decimal("0.60") -> "0.6", Decimal("100.00") -> "100"
        This ensures consistent formatting in API responses without scientific notation.
        """
        # Convert to string and strip trailing zeros and decimal point if not needed
        # This avoids scientific notation (e.g., "1E+2") from normalize()
        result = str(value)
        if "." in result:
            result = result.rstrip("0").rstrip(".")
        return result

    class Config:
        """Pydantic config."""

        from_attributes = True


class GridConfigBase(BaseModel):
    """Base schema for grid configuration."""

    spacing_type: str = Field(
        pattern="^(fixed|percentage)$", description="Grid spacing type (fixed or percentage)"
    )
    spacing_value: Decimal = Field(gt=0, description="Grid spacing value")
    range_percent: Decimal = Field(gt=0, description="Grid range as percentage from current price")
    max_total_orders: int = Field(gt=0, description="Maximum number of simultaneous limit orders")
    anchor_mode: str = Field(
        pattern="^(none|hundred)$", description="Grid anchor mode (none or hundred)"
    )
    anchor_value: Decimal = Field(gt=0, description="Anchor value for grid alignment")

    @field_validator("spacing_type")
    @classmethod
    def validate_spacing_type(cls, v: str) -> str:
        """Validate spacing type is either fixed or percentage."""
        if v not in ["fixed", "percentage"]:
            raise ValueError("spacing_type must be 'fixed' or 'percentage'")
        return v

    @field_validator("anchor_mode")
    @classmethod
    def validate_anchor_mode(cls, v: str) -> str:
        """Validate anchor mode is either none or hundred."""
        if v not in ["none", "hundred"]:
            raise ValueError("anchor_mode must be 'none' or 'hundred'")
        return v


class GridConfigUpdate(BaseModel):
    """Schema for partial grid configuration updates (PATCH)."""

    spacing_type: str | None = Field(
        default=None, pattern="^(fixed|percentage)$", description="Grid spacing type"
    )
    spacing_value: Decimal | None = Field(default=None, gt=0, description="Grid spacing value")
    range_percent: Decimal | None = Field(
        default=None, gt=0, description="Grid range as percentage"
    )
    max_total_orders: int | None = Field(default=None, gt=0, description="Maximum number of orders")
    anchor_mode: str | None = Field(
        default=None, pattern="^(none|hundred)$", description="Grid anchor mode"
    )
    anchor_value: Decimal | None = Field(default=None, gt=0, description="Anchor value")

    @field_validator("spacing_type")
    @classmethod
    def validate_spacing_type(cls, v: str | None) -> str | None:
        """Validate spacing type is either fixed or percentage."""
        if v is not None and v not in ["fixed", "percentage"]:
            raise ValueError("spacing_type must be 'fixed' or 'percentage'")
        return v

    @field_validator("anchor_mode")
    @classmethod
    def validate_anchor_mode(cls, v: str | None) -> str | None:
        """Validate anchor mode is either none or hundred."""
        if v is not None and v not in ["none", "hundred"]:
            raise ValueError("anchor_mode must be 'none' or 'hundred'")
        return v


class GridConfigResponse(BaseModel):
    """Response schema for grid configuration."""

    id: str
    account_id: str
    spacing_type: str
    spacing_value: Decimal
    range_percent: Decimal
    max_total_orders: int
    anchor_mode: str
    anchor_value: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("spacing_value", "range_percent", "anchor_value")
    def serialize_decimal(self, value: Decimal) -> str:
        """Normalize Decimal values to remove trailing zeros.

        Example: Decimal("100.00") -> "100", Decimal("2.50") -> "2.5"
        This ensures consistent formatting in API responses without scientific notation.
        """
        # Convert to string and strip trailing zeros and decimal point if not needed
        # This avoids scientific notation (e.g., "1E+2") from normalize()
        result = str(value)
        if "." in result:
            result = result.rstrip("0").rstrip(".")
        return result

    class Config:
        """Pydantic config."""

        from_attributes = True
