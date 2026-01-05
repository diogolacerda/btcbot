"""Pydantic schemas for activity events API responses."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class EventTypeEnum(str, Enum):
    """Event type enum for API responses."""

    ORDER_FILLED = "ORDER_FILLED"
    TRADE_CLOSED = "TRADE_CLOSED"
    STRATEGY_PAUSED = "STRATEGY_PAUSED"
    STRATEGY_RESUMED = "STRATEGY_RESUMED"
    TP_ADJUSTED = "TP_ADJUSTED"
    CYCLE_ACTIVATED = "CYCLE_ACTIVATED"
    CYCLE_DEACTIVATED = "CYCLE_DEACTIVATED"
    BOT_STARTED = "BOT_STARTED"
    BOT_STOPPED = "BOT_STOPPED"
    ERROR_OCCURRED = "ERROR_OCCURRED"


class TimePeriodEnum(str, Enum):
    """Predefined time period filters."""

    TODAY = "today"
    SEVEN_DAYS = "7days"
    THIRTY_DAYS = "30days"
    CUSTOM = "custom"


class ActivityEventSchema(BaseModel):
    """Schema for an activity event."""

    id: UUID = Field(..., description="Event unique identifier")
    event_type: EventTypeEnum = Field(..., description="Type of event")
    description: str = Field(..., description="Human-readable event description")
    event_data: dict | None = Field(None, description="Additional event metadata")
    timestamp: datetime = Field(..., description="When the event occurred")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "ORDER_FILLED",
                "description": "Grid order filled at $95,000.00",
                "event_data": {
                    "order_id": "123456789",
                    "price": "95000.00",
                    "quantity": "0.001",
                },
                "timestamp": "2026-01-05T10:00:00Z",
            }
        },
    }


class ActivityEventsListResponse(BaseModel):
    """Response schema for list of activity events."""

    events: list[ActivityEventSchema] = Field(..., description="List of activity events")
    total: int = Field(..., description="Total number of events matching filter")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")

    model_config = {
        "json_schema_extra": {
            "example": {
                "events": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "event_type": "ORDER_FILLED",
                        "description": "Grid order filled at $95,000.00",
                        "event_data": {"order_id": "123456789", "price": "95000.00"},
                        "timestamp": "2026-01-05T10:00:00Z",
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0,
            }
        },
    }
