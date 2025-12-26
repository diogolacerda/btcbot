from __future__ import annotations

import asyncio
import gzip
import json
import time
from collections.abc import Callable
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

from config import BingXConfig
from src.utils.logger import main_logger, orders_logger


class BingXWebSocket:
    """
    WebSocket client for BingX market data.

    Subscribes to:
    - Kline data for MACD calculation
    - Price updates for grid management
    """

    def __init__(self, config: BingXConfig):
        self.ws_url = config.ws_url
        self._ws: Any = None
        self._running = False
        self._subscriptions: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._reconnect_delay: float = 1.0
        self._max_reconnect_delay: float = 60.0

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        self._running = True
        await self._connect_loop()

    async def _connect_loop(self) -> None:
        """Main connection loop with auto-reconnect."""
        while self._running:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=None,  # Disable library ping, use server's ping/pong
                    ping_timeout=None,
                    close_timeout=5,
                ) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0
                    main_logger.info("WebSocket conectado")

                    # Resubscribe to all channels
                    await self._resubscribe()

                    # Process messages
                    await self._message_loop()

            except ConnectionClosed as e:
                main_logger.warning(f"WebSocket desconectado: {e}")
            except Exception as e:
                main_logger.error(f"Erro WebSocket: {e}")

            if self._running:
                main_logger.info(f"Reconectando em {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay,
                )

    async def _message_loop(self) -> None:
        """Process incoming messages."""
        assert self._ws is not None
        async for message in self._ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                main_logger.warning(f"Invalid JSON: {message!r}")
            except Exception as e:
                main_logger.error(f"Error processing message: {e}")

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        # Handle ping/pong
        if data.get("ping"):
            await self._send({"pong": data["ping"]})
            return

        # Handle subscription response
        if data.get("id"):
            main_logger.debug(f"Subscription response: {data}")
            return

        # Handle data updates
        data_type = data.get("dataType", "")
        if data_type in self._subscriptions:
            callback = self._subscriptions[data_type]
            try:
                callback(data.get("data", data))
            except Exception as e:
                main_logger.error(f"Callback error for {data_type}: {e}")

    async def _send(self, data: dict) -> None:
        """Send message to WebSocket."""
        if self._ws and self._ws.open:
            await self._ws.send(json.dumps(data))

    async def _resubscribe(self) -> None:
        """Resubscribe to all channels after reconnect."""
        for data_type in self._subscriptions.keys():
            await self._subscribe_channel(data_type)

    async def _subscribe_channel(self, data_type: str) -> None:
        """Subscribe to a specific channel."""
        message = {
            "id": f"sub_{int(time.time() * 1000)}",
            "reqType": "sub",
            "dataType": data_type,
        }
        await self._send(message)
        main_logger.debug(f"Subscribed to: {data_type}")

    async def subscribe_kline(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[dict], None],
    ) -> None:
        """
        Subscribe to kline/candlestick updates.

        Args:
            symbol: Trading pair (e.g., "BTC-USDT")
            interval: Kline interval (1m, 5m, 15m, 1h, etc.)
            callback: Function to call with kline data
        """
        data_type = f"{symbol}@kline_{interval}"
        self._subscriptions[data_type] = callback

        if self._ws and self._ws.open:
            await self._subscribe_channel(data_type)

    async def subscribe_price(
        self,
        symbol: str,
        callback: Callable[[float], None],
    ) -> None:
        """
        Subscribe to price updates.

        Args:
            symbol: Trading pair
            callback: Function to call with new price
        """
        data_type = f"{symbol}@trade"

        def price_callback(data: dict) -> None:
            if isinstance(data, dict) and "p" in data:
                price = float(data["p"])
                callback(price)

        self._subscriptions[data_type] = price_callback

        if self._ws and self._ws.open:
            await self._subscribe_channel(data_type)

    async def subscribe_depth(
        self,
        symbol: str,
        callback: Callable[[dict], None],
    ) -> None:
        """
        Subscribe to order book depth updates.

        Args:
            symbol: Trading pair
            callback: Function to call with depth data
        """
        data_type = f"{symbol}@depth"
        self._subscriptions[data_type] = callback

        if self._ws and self._ws.open:
            await self._subscribe_channel(data_type)

    async def unsubscribe(self, data_type: str) -> None:
        """Unsubscribe from a channel."""
        if data_type in self._subscriptions:
            del self._subscriptions[data_type]

            if self._ws and self._ws.open:
                message = {
                    "id": f"unsub_{int(time.time() * 1000)}",
                    "reqType": "unsub",
                    "dataType": data_type,
                }
                await self._send(message)

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._running = False
        if self._ws:
            await self._ws.close()
        main_logger.info("WebSocket desconectado")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        if self._ws is None:
            return False
        try:
            return str(self._ws.state.name) == "OPEN"
        except Exception:
            return False


class BingXAccountWebSocket:
    """
    WebSocket client for BingX account updates (orders, positions).

    Requires listenKey for authentication.
    Receives real-time updates for:
    - Order fills
    - Order cancellations
    - Position changes
    """

    def __init__(self, listen_key: str):
        self._listen_key = listen_key
        self._ws: Any = None
        self._running = False
        self._reconnect_delay: float = 1.0
        self._max_reconnect_delay: float = 60.0
        self._listen_key_expired = False
        self._renewal_in_progress = False  # Prevent duplicate renewal calls

        # Callbacks
        self._on_order_update: Callable[[dict[str, Any]], None] | None = None
        self._on_position_update: Callable[[dict[str, Any]], None] | None = None
        self._on_account_update: Callable[[dict[str, Any]], None] | None = None
        self._on_listen_key_expired: Callable[[], None] | None = None

    @property
    def ws_url(self) -> str:
        return f"wss://open-api-ws.bingx.com/market?listenKey={self._listen_key}"

    def update_listen_key(self, new_key: str) -> None:
        """Update listenKey for reconnection."""
        self._listen_key = new_key
        self._listen_key_expired = False
        self._renewal_in_progress = False  # Reset flag to allow future renewals
        main_logger.info("ListenKey atualizado no WebSocket client")

    def set_listen_key_expired_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for when listenKey expires."""
        self._on_listen_key_expired = callback

    def set_order_callback(self, callback: Callable[[dict], None]) -> None:
        """Set callback for order updates."""
        self._on_order_update = callback

    def set_position_callback(self, callback: Callable[[dict], None]) -> None:
        """Set callback for position updates."""
        self._on_position_update = callback

    def set_account_callback(self, callback: Callable[[dict], None]) -> None:
        """Set callback for account/balance updates."""
        self._on_account_update = callback

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        self._running = True
        await self._connect_loop()

    async def _connect_loop(self) -> None:
        """Main connection loop with auto-reconnect."""
        while self._running:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=None,  # Disable library ping, use server's ping/pong
                    ping_timeout=None,
                    close_timeout=5,  # Don't wait forever for close
                    max_size=10_485_760,  # 10MB max message size
                ) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0
                    main_logger.info("Account WebSocket conectado")

                    # Process messages
                    await self._message_loop()

            except ConnectionClosed as e:
                # Log disconnections but with more detail for debugging
                if self._running:
                    # Check if it's a normal close or error
                    if hasattr(e, "code") and e.code in [1000, 1001]:
                        # Normal close or going away - just debug
                        main_logger.debug(
                            f"Account WebSocket desconectado normalmente: code={e.code}"
                        )
                    else:
                        # Unexpected disconnection - log as warning for investigation
                        main_logger.info(f"Account WebSocket desconectado: {e}")
            except TimeoutError:
                main_logger.warning("Account WebSocket timeout - reconectando...")
            except Exception as e:
                main_logger.error(f"Erro Account WebSocket: {e}")

            if self._running:
                # Short delay for normal reconnects, don't log excessively
                await asyncio.sleep(min(2, self._reconnect_delay))
                self._reconnect_delay = min(
                    self._reconnect_delay * 1.5,  # Slower backoff
                    self._max_reconnect_delay,
                )

    async def _message_loop(self) -> None:
        """Process incoming messages."""
        assert self._ws is not None
        async for message in self._ws:
            try:
                # BingX sends GZIP compressed data
                if isinstance(message, bytes):
                    try:
                        message = gzip.decompress(message).decode("utf-8")
                    except Exception:
                        pass  # Not compressed

                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                main_logger.warning(f"Invalid JSON: {message[:100]!r}")
            except Exception as e:
                main_logger.error(f"Error processing account message: {e}")

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        # Handle ping/pong
        if "ping" in data:
            await self._send({"pong": data["ping"]})
            return

        if "Ping" in data:
            await self._send({"Pong": data["Ping"]})
            return

        # Get event type
        event_type = data.get("e", "")

        # Log only important events to avoid spam
        if event_type in ["ORDER_TRADE_UPDATE", "ACCOUNT_UPDATE", "listenKeyExpired"]:
            orders_logger.debug(f"WS Event: {event_type}")

        # Order update event
        if event_type == "ORDER_TRADE_UPDATE":
            order_data = data.get("o", {})
            orders_logger.info(f"WS Order Update: {order_data.get('X')} - {order_data.get('i')}")

            if self._on_order_update:
                self._on_order_update(order_data)

        # Account/Position update event
        elif event_type == "ACCOUNT_UPDATE":
            update_data = data.get("a", {})

            # Position updates
            positions = update_data.get("P", [])
            if positions and self._on_position_update:
                for pos in positions:
                    self._on_position_update(pos)

            # Balance updates
            balances = update_data.get("B", [])
            if balances and self._on_account_update:
                for bal in balances:
                    self._on_account_update(bal)

        # Listen key expired (can come in different formats)
        elif event_type == "listenKeyExpired" or data.get("dataType") == "public.listenKeyExpired":
            # Only trigger renewal once per expiration event
            if not self._renewal_in_progress:
                self._renewal_in_progress = True
                self._listen_key_expired = True
                main_logger.warning("ListenKey expirado detectado pelo WebSocket")
                if self._on_listen_key_expired:
                    self._on_listen_key_expired()

    async def _send(self, data: dict) -> None:
        """Send message to WebSocket."""
        if self._ws and self._ws.open:
            await self._ws.send(json.dumps(data))

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._running = False
        if self._ws:
            await self._ws.close()
        main_logger.info("Account WebSocket desconectado")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        if self._ws is None:
            return False
        try:
            return str(self._ws.state.name) == "OPEN"
        except Exception:
            return False
