"""WebSocket event types for dashboard real-time updates.

This module defines the event types and data structures for WebSocket
communication between the bot and dashboard clients.

Event Types:
- bot_status: Bot state changes (ACTIVE, PAUSED, etc.)
- position_update: Position changes (new fills, closures)
- order_update: Order status changes (placed, filled, cancelled)
- price_update: Current BTC price updates
- activity_event: Activity log events from the bot
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class WebSocketEventType(str, Enum):
    """Types of WebSocket events."""

    BOT_STATUS = "bot_status"
    POSITION_UPDATE = "position_update"
    ORDER_UPDATE = "order_update"
    PRICE_UPDATE = "price_update"
    ACTIVITY_EVENT = "activity_event"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    # Connection lifecycle events
    CONNECTION_ESTABLISHED = "connection_established"
    PONG = "pong"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"


class BotStatusEvent(BaseModel):
    """Bot status update event data."""

    model_config = ConfigDict(use_enum_values=True)

    state: str  # WAIT, ACTIVATE, ACTIVE, PAUSE, INACTIVE
    is_running: bool
    macd_trend: str | None = None  # bullish, bearish, neutral
    grid_active: bool = False
    pending_orders_count: int = 0
    filled_orders_count: int = 0
    # MACD indicator values
    macd_line: float | None = None
    histogram: float | None = None
    signal_line: float | None = None


class PositionUpdateEvent(BaseModel):
    """Position update event data."""

    model_config = ConfigDict(use_enum_values=True)

    symbol: str
    side: str  # LONG, SHORT
    size: str  # Decimal as string for JSON
    entry_price: str
    current_price: str
    unrealized_pnl: str
    leverage: int
    timestamp: datetime


class OrderUpdateEvent(BaseModel):
    """Order update event data."""

    model_config = ConfigDict(use_enum_values=True)

    order_id: str
    symbol: str
    side: str  # LONG, SHORT
    order_type: str  # LIMIT, MARKET, TAKE_PROFIT_MARKET
    status: str  # PENDING, FILLED, CANCELLED, TP_HIT
    price: str  # Entry price
    tp_price: str | None = None  # Take profit price
    quantity: str
    filled_quantity: str
    created_at: datetime
    filled_at: datetime | None = None
    closed_at: datetime | None = None
    exchange_tp_order_id: str | None = None  # TP order ID from exchange


class PriceUpdateEvent(BaseModel):
    """Price update event data."""

    model_config = ConfigDict(use_enum_values=True)

    symbol: str
    price: str
    change_24h: str | None = None
    change_percent_24h: str | None = None
    volume_24h: str | None = None
    timestamp: datetime


class ActivityEventData(BaseModel):
    """Activity event data for logging bot actions."""

    model_config = ConfigDict(use_enum_values=True)

    event_type: str
    message: str
    severity: str = "info"  # info, warning, error, success
    metadata: dict[str, Any] | None = None
    timestamp: datetime


class HeartbeatEvent(BaseModel):
    """Heartbeat event to maintain connection health."""

    timestamp: datetime
    server_time: datetime


class ErrorEvent(BaseModel):
    """Error event for WebSocket errors."""

    code: str
    message: str
    timestamp: datetime


class WebSocketEvent(BaseModel):
    """Generic WebSocket event wrapper.

    All events sent through WebSocket are wrapped in this structure.
    """

    model_config = ConfigDict(use_enum_values=True)

    type: WebSocketEventType
    data: (
        BotStatusEvent
        | PositionUpdateEvent
        | OrderUpdateEvent
        | PriceUpdateEvent
        | ActivityEventData
        | HeartbeatEvent
        | ErrorEvent
        | dict[str, Any]
    )
    timestamp: datetime

    @classmethod
    def bot_status(cls, data: BotStatusEvent) -> "WebSocketEvent":
        """Create a bot status event."""
        return cls(
            type=WebSocketEventType.BOT_STATUS,
            data=data,
            timestamp=datetime.now(),
        )

    @classmethod
    def position_update(cls, data: PositionUpdateEvent) -> "WebSocketEvent":
        """Create a position update event."""
        return cls(
            type=WebSocketEventType.POSITION_UPDATE,
            data=data,
            timestamp=datetime.now(),
        )

    @classmethod
    def order_update(cls, data: OrderUpdateEvent) -> "WebSocketEvent":
        """Create an order update event."""
        return cls(
            type=WebSocketEventType.ORDER_UPDATE,
            data=data,
            timestamp=datetime.now(),
        )

    @classmethod
    def price_update(cls, data: PriceUpdateEvent) -> "WebSocketEvent":
        """Create a price update event."""
        return cls(
            type=WebSocketEventType.PRICE_UPDATE,
            data=data,
            timestamp=datetime.now(),
        )

    @classmethod
    def activity_event(cls, data: ActivityEventData) -> "WebSocketEvent":
        """Create an activity event."""
        return cls(
            type=WebSocketEventType.ACTIVITY_EVENT,
            data=data,
            timestamp=datetime.now(),
        )

    @classmethod
    def heartbeat(cls) -> "WebSocketEvent":
        """Create a heartbeat event."""
        now = datetime.now()
        return cls(
            type=WebSocketEventType.HEARTBEAT,
            data=HeartbeatEvent(timestamp=now, server_time=now),
            timestamp=now,
        )

    @classmethod
    def error(cls, code: str, message: str) -> "WebSocketEvent":
        """Create an error event."""
        return cls(
            type=WebSocketEventType.ERROR,
            data=ErrorEvent(code=code, message=message, timestamp=datetime.now()),
            timestamp=datetime.now(),
        )
