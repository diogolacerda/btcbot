"""Real-time BTC price streaming service.

This service connects to BingX market WebSocket, subscribes to BTC-USDT
trade updates, and broadcasts price changes to connected dashboard clients
via WebSocket.

Key features:
- Auto-reconnects on connection loss
- Throttling to prevent spam (1s interval, 0.01% price change)
- Only broadcasts when clients are connected
- Graceful lifecycle management
"""

import asyncio
from decimal import Decimal

from config import BingXConfig
from src.api.routes.market_data import PriceBroadcastThrottler
from src.api.websocket.connection_manager import get_connection_manager
from src.api.websocket.events import PriceUpdateEvent, WebSocketEvent
from src.client.websocket_client import BingXWebSocket
from src.utils.logger import main_logger as logger


class PriceStreamer:
    """Streams real-time BTC price updates to dashboard clients.

    Connects to BingX market WebSocket, subscribes to BTC-USDT trade stream,
    applies throttling, and broadcasts price updates via ConnectionManager.
    """

    def __init__(self, config: BingXConfig, symbol: str = "BTC-USDT"):
        """Initialize price streamer.

        Args:
            config: BingX configuration with WebSocket URL
            symbol: Trading symbol to stream (default: BTC-USDT)
        """
        self.symbol = symbol
        self._ws_client = BingXWebSocket(config)
        self._connection_manager = get_connection_manager()
        self._throttler = PriceBroadcastThrottler(
            min_interval_seconds=1.0,  # Max 1 broadcast per second
            min_change_percent=0.01,  # Min 0.01% price change
        )
        self._stream_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """Start the price streaming service.

        Connects to BingX WebSocket and subscribes to price updates.
        Creates an async task to manage the connection lifecycle.
        """
        if self._running:
            logger.warning("Price streamer already running")
            return

        self._running = True
        self._stream_task = asyncio.create_task(self._run())
        logger.info(f"Price streamer started for {self.symbol}")

    async def stop(self) -> None:
        """Stop the price streaming service.

        Disconnects from BingX WebSocket and cancels the streaming task.
        """
        self._running = False

        if self._ws_client.is_connected:
            await self._ws_client.disconnect()

        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

        logger.info("Price streamer stopped")

    async def _run(self) -> None:
        """Main streaming loop.

        Connects to WebSocket and subscribes to price updates.
        The WebSocket client handles auto-reconnection internally.
        """
        try:
            # Subscribe to price updates before connecting
            # The subscription will be activated after connection
            await self._ws_client.subscribe_price(
                symbol=self.symbol,
                callback=self._handle_price_update,
            )

            # Connect to WebSocket (blocks until disconnection)
            await self._ws_client.connect()

        except asyncio.CancelledError:
            logger.info("Price stream cancelled")
        except Exception as e:
            logger.error(f"Price stream error: {e}")

    def _handle_price_update(self, price: float) -> None:
        """Handle incoming price update from WebSocket.

        Applies throttling and broadcasts to connected clients if conditions met.

        Args:
            price: Current BTC price from trade stream
        """
        # Skip if no clients connected
        if self._connection_manager.active_connections_count == 0:
            return

        current_price = Decimal(str(price))

        # Apply throttling
        should_broadcast, throttle_reason = self._throttler.should_broadcast(current_price)

        if not should_broadcast:
            logger.debug(f"Price update throttled: {throttle_reason}")
            return

        # Create price update event
        # Note: trade stream doesn't include 24h stats, only current price
        from datetime import UTC, datetime

        price_event = PriceUpdateEvent(
            symbol=self.symbol,
            price=str(current_price),
            timestamp=datetime.now(UTC),
        )

        # Broadcast to all connected clients (fire-and-forget)
        asyncio.create_task(
            self._connection_manager.broadcast(WebSocketEvent.price_update(price_event))
        )

        logger.debug(f"Price update broadcast: {self.symbol} @ ${current_price}")
