"""Thread-based WebSocket client wrapper for sync architecture."""

import asyncio
import queue
import threading
from collections.abc import Callable
from typing import Any

from config import BingXConfig
from src.client.websocket_client import BingXAccountWebSocket, BingXWebSocket
from src.utils.logger import main_logger


class WebSocketThread(threading.Thread):
    """
    Thread wrapper for async WebSocket client.

    Runs WebSocket connection in a separate thread with its own asyncio event loop.
    Messages are passed to main thread via queue.Queue for thread-safe communication.
    """

    def __init__(self, config: BingXConfig):
        super().__init__(daemon=True, name="WebSocketThread")
        self.config = config
        self.message_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()
        self._ws_client: BingXWebSocket | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def run(self) -> None:
        """Thread entry point - creates event loop and runs WebSocket."""
        try:
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Create WebSocket client
            self._ws_client = BingXWebSocket(self.config)

            # Run until stopped
            self._loop.run_until_complete(self._run_websocket())
        except Exception as e:
            main_logger.error(f"WebSocket thread error: {e}")
        finally:
            if self._loop:
                self._loop.close()

    async def _run_websocket(self) -> None:
        """Run WebSocket connection."""
        if not self._ws_client:
            return

        try:
            await self._ws_client.connect()
        except asyncio.CancelledError:
            main_logger.info("WebSocket cancelled")
        except Exception as e:
            main_logger.error(f"WebSocket error: {e}")

    def stop(self) -> None:
        """Stop WebSocket thread."""
        self._stop_event.set()
        if self._ws_client and self._loop:
            # Schedule disconnect in the WebSocket's event loop
            asyncio.run_coroutine_threadsafe(self._ws_client.disconnect(), self._loop)

    def subscribe_kline(self, symbol: str, interval: str, callback: Callable[[dict], None]) -> None:
        """Subscribe to kline updates (thread-safe)."""
        if not self._ws_client or not self._loop:
            return

        def queue_callback(data: dict) -> None:
            """Wrap callback to put data in queue."""
            self.message_queue.put({"type": "kline", "data": data})
            # Also call original callback directly (it's already in the WS thread)
            callback(data)

        # Schedule subscription in WebSocket's event loop
        asyncio.run_coroutine_threadsafe(
            self._ws_client.subscribe_kline(symbol, interval, queue_callback),
            self._loop,
        )

    def subscribe_price(self, symbol: str, callback: Callable[[float], None]) -> None:
        """Subscribe to price updates (thread-safe)."""
        if not self._ws_client or not self._loop:
            return

        def queue_callback(price: float) -> None:
            """Wrap callback to put price in queue."""
            self.message_queue.put({"type": "price", "data": price})
            callback(price)

        asyncio.run_coroutine_threadsafe(
            self._ws_client.subscribe_price(symbol, queue_callback),
            self._loop,
        )

    def get_message_nowait(self) -> dict[str, Any] | None:
        """Get message from queue without blocking (sync, for main loop)."""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected (thread-safe)."""
        return self._ws_client.is_connected if self._ws_client else False


class AccountWebSocketThread(threading.Thread):
    """
    Thread wrapper for account WebSocket client.

    Handles order and position updates via message queue.
    """

    def __init__(self, listen_key: str):
        super().__init__(daemon=True, name="AccountWebSocketThread")
        self._listen_key = listen_key
        self.message_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()
        self._ws_client: BingXAccountWebSocket | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def run(self) -> None:
        """Thread entry point."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._ws_client = BingXAccountWebSocket(self._listen_key)

            # Set up callbacks to put messages in queue
            self._ws_client.set_order_callback(self._queue_order_update)
            self._ws_client.set_position_callback(self._queue_position_update)
            self._ws_client.set_account_callback(self._queue_account_update)

            self._loop.run_until_complete(self._run_websocket())
        except Exception as e:
            main_logger.error(f"Account WebSocket thread error: {e}")
        finally:
            if self._loop:
                self._loop.close()

    async def _run_websocket(self) -> None:
        """Run account WebSocket connection."""
        if not self._ws_client:
            return

        try:
            await self._ws_client.connect()
        except asyncio.CancelledError:
            main_logger.info("Account WebSocket cancelled")
        except Exception as e:
            main_logger.error(f"Account WebSocket error: {e}")

    def _queue_order_update(self, data: dict) -> None:
        """Queue order update for main thread."""
        self.message_queue.put({"type": "order_update", "data": data})

    def _queue_position_update(self, data: dict) -> None:
        """Queue position update for main thread."""
        self.message_queue.put({"type": "position_update", "data": data})

    def _queue_account_update(self, data: dict) -> None:
        """Queue account update for main thread."""
        self.message_queue.put({"type": "account_update", "data": data})

    def update_listen_key(self, new_key: str) -> None:
        """Update listen key (thread-safe)."""
        if self._ws_client:
            self._ws_client.update_listen_key(new_key)

    def set_listen_key_expired_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for listen key expiration."""
        if self._ws_client:
            self._ws_client.set_listen_key_expired_callback(callback)

    def stop(self) -> None:
        """Stop account WebSocket thread."""
        self._stop_event.set()
        if self._ws_client and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws_client.disconnect(), self._loop)

    def get_message_nowait(self) -> dict[str, Any] | None:
        """Get message from queue without blocking."""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    @property
    def is_connected(self) -> bool:
        """Check if account WebSocket is connected."""
        return self._ws_client.is_connected if self._ws_client else False
