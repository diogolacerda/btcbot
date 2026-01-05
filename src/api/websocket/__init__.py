"""WebSocket module for real-time dashboard updates."""

from src.api.websocket import dashboard_ws
from src.api.websocket.connection_manager import ConnectionManager, get_connection_manager
from src.api.websocket.events import (
    ActivityEventData,
    BotStatusEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    PriceUpdateEvent,
    WebSocketEvent,
    WebSocketEventType,
)

__all__ = [
    "ConnectionManager",
    "get_connection_manager",
    "dashboard_ws",
    "WebSocketEvent",
    "WebSocketEventType",
    "BotStatusEvent",
    "PositionUpdateEvent",
    "OrderUpdateEvent",
    "PriceUpdateEvent",
    "ActivityEventData",
]
