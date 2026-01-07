"""Schemas for Strategy API endpoints."""

from datetime import datetime
from decimal import Decimal

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
    anchor_mode: str = Field(
        default="none", description="Grid anchor mode (none, hundred, thousand)"
    )
    anchor_threshold: Decimal = Field(
        default=Decimal("100.0"), gt=0, description="Anchor threshold"
    )

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

    @field_validator("anchor_mode")
    @classmethod
    def validate_anchor_mode(cls, v: str) -> str:
        """Validate anchor mode."""
        v_lower = v.lower()
        if v_lower not in ["none", "hundred", "thousand"]:
            raise ValueError("anchor_mode must be 'none', 'hundred', or 'thousand'")
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
    anchor_mode: str | None = Field(default=None, description="Grid anchor mode")
    anchor_threshold: Decimal | None = Field(default=None, gt=0, description="Anchor threshold")

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

    @field_validator("anchor_mode")
    @classmethod
    def validate_anchor_mode(cls, v: str | None) -> str | None:
        """Validate anchor mode."""
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["none", "hundred", "thousand"]:
                raise ValueError("anchor_mode must be 'none', 'hundred', or 'thousand'")
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
    anchor_mode: str
    anchor_threshold: Decimal

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
        "anchor_threshold",
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
