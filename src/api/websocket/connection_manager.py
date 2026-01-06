"""WebSocket connection manager for handling multiple clients.

This module provides a singleton ConnectionManager that:
- Tracks active WebSocket connections
- Broadcasts events to all connected clients
- Handles connection lifecycle (connect, disconnect, reconnect)
- Provides heartbeat functionality for connection health
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel

from src.api.websocket.events import WebSocketEvent

logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""

    user_email: str
    connected_at: datetime
    last_heartbeat: datetime


class ConnectionManager:
    """Manages WebSocket connections for the dashboard.

    This is a singleton class that maintains all active WebSocket connections
    and provides methods for broadcasting events to connected clients.
    """

    _instance: "ConnectionManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "ConnectionManager":
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize connection manager."""
        if self._initialized:
            return

        self._active_connections: dict[WebSocket, ConnectionInfo] = {}
        self._heartbeat_interval: int = 30  # seconds
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        ConnectionManager._initialized = True
        logger.info("ConnectionManager initialized")

    @property
    def active_connections_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket, user_email: str) -> None:
        """Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection to accept.
            user_email: Email of the authenticated user.
        """
        await websocket.accept()

        # Start heartbeat on first connection
        is_first_connection = self.active_connections_count == 0

        async with self._lock:
            now = datetime.now()
            self._active_connections[websocket] = ConnectionInfo(
                user_email=user_email,
                connected_at=now,
                last_heartbeat=now,
            )

        if is_first_connection:
            await self.start_heartbeat()

        logger.info(
            f"WebSocket connected: {user_email} "
            f"(total connections: {self.active_connections_count})"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove.
        """
        async with self._lock:
            if websocket in self._active_connections:
                info = self._active_connections.pop(websocket)
                logger.info(
                    f"WebSocket disconnected: {info.user_email} "
                    f"(total connections: {self.active_connections_count})"
                )

        # Stop heartbeat when no more connections
        if self.active_connections_count == 0:
            await self.stop_heartbeat()

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event: WebSocket event to broadcast.
        """
        if not self._active_connections:
            return

        message = event.model_dump_json()
        disconnected: list[WebSocket] = []

        async with self._lock:
            for websocket in self._active_connections:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def send_personal(self, websocket: WebSocket, event: WebSocketEvent) -> None:
        """Send an event to a specific client.

        Args:
            websocket: Target WebSocket connection.
            event: WebSocket event to send.
        """
        try:
            await websocket.send_text(event.model_dump_json())
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast_json(self, data: dict[str, Any]) -> None:
        """Broadcast raw JSON data to all connected clients.

        Args:
            data: Dictionary to serialize and send.
        """
        if not self._active_connections:
            return

        disconnected: list[WebSocket] = []

        async with self._lock:
            for websocket in self._active_connections:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send JSON to client: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)

    def update_heartbeat(self, websocket: WebSocket) -> None:
        """Update last heartbeat time for a connection.

        Args:
            websocket: WebSocket connection to update.
        """
        if websocket in self._active_connections:
            self._active_connections[websocket].last_heartbeat = datetime.now()

    async def start_heartbeat(self) -> None:
        """Start the heartbeat broadcast task."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("Heartbeat task started")

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat broadcast task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat task stopped")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat events to all clients."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self._active_connections:
                    await self.broadcast(WebSocketEvent.heartbeat())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    def get_connection_stats(self) -> dict[str, Any]:
        """Get statistics about current connections.

        Returns:
            Dictionary with connection statistics.
        """
        return {
            "total_connections": self.active_connections_count,
            "connections": [
                {
                    "user_email": info.user_email,
                    "connected_at": info.connected_at.isoformat(),
                    "last_heartbeat": info.last_heartbeat.isoformat(),
                }
                for info in self._active_connections.values()
            ],
        }


# Global singleton instance
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance.

    Returns:
        ConnectionManager instance.
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
