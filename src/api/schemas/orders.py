"""Pydantic schemas for orders API responses."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatusEnum(str, Enum):
    """Order status enum for API responses."""

    PENDING = "PENDING"
    FILLED = "FILLED"
    TP_HIT = "TP_HIT"
    CANCELLED = "CANCELLED"


class OrderSchema(BaseModel):
    """Schema for a grid order."""

    order_id: str = Field(..., description="Exchange order ID")
    price: Decimal = Field(..., description="Entry price")
    tp_price: Decimal = Field(..., description="Take profit price")
    quantity: Decimal = Field(..., description="Order quantity")
    side: str = Field(default="LONG", description="Order side (LONG or SHORT)")
    status: OrderStatusEnum = Field(..., description="Order status")
    created_at: datetime = Field(..., description="Order creation timestamp")
    filled_at: datetime | None = Field(None, description="Order fill timestamp")
    closed_at: datetime | None = Field(None, description="Order close timestamp")
    exchange_tp_order_id: str | None = Field(None, description="TP order ID from exchange")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "order_id": "123456789",
                "price": "95000.00",
                "tp_price": "95500.00",
                "quantity": "0.001",
                "side": "LONG",
                "status": "PENDING",
                "created_at": "2026-01-05T10:00:00Z",
                "filled_at": None,
                "closed_at": None,
                "exchange_tp_order_id": None,
            }
        },
    }


class OrdersListResponse(BaseModel):
    """Response schema for list of orders."""

    orders: list[OrderSchema] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders matching filter")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    pending_count: int = Field(..., description="Count of pending orders")
    filled_count: int = Field(..., description="Count of filled orders (open positions)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "orders": [
                    {
                        "order_id": "123456789",
                        "price": "95000.00",
                        "tp_price": "95500.00",
                        "quantity": "0.001",
                        "side": "LONG",
                        "status": "PENDING",
                        "created_at": "2026-01-05T10:00:00Z",
                        "filled_at": None,
                        "closed_at": None,
                        "exchange_tp_order_id": None,
                    }
                ],
                "total": 10,
                "limit": 100,
                "offset": 0,
                "pending_count": 5,
                "filled_count": 5,
            }
        },
    }
