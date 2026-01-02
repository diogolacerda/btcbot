import hashlib
import hmac
import json
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import httpx
import pandas as pd

from config import BingXConfig
from src.utils.logger import error_logger, orders_logger


class BingXClient:
    """Client for BingX Perpetual Swap API v2."""

    def __init__(self, config: BingXConfig):
        self.config = config
        self.base_url = config.base_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Cache com TTL (time to live) em segundos
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = {
            "klines": 60,  # Klines: 60s (muda só no candle novo)
            "balance": 30,  # Balance: 30s
            "positions": 15,  # Positions: 15s
            "open_orders": 15,  # Open orders: 15s
            "funding_rate": 300,  # Funding rate: 5min (não muda frequentemente)
        }

    def _get_cached(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        if key in self._cache:
            cached_time, value = self._cache[key]
            ttl = self._cache_ttl.get(key, 10)
            if time.time() - cached_time < ttl:
                return value
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache value."""
        self._cache[key] = (time.time(), value)

    def _invalidate_cache(self, *prefixes: str) -> None:
        """Invalidate cache entries matching prefixes."""
        keys_to_delete = [
            k for k in self._cache if any(k.startswith(p) or k == p for p in prefixes)
        ]
        for k in keys_to_delete:
            del self._cache[k]

    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for request."""
        signature = hmac.new(
            self.config.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get_headers(self) -> dict:
        """Get request headers with API key."""
        return {
            "X-BX-APIKEY": self.config.api_key,
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """Make authenticated request to BingX API."""
        params = params or {}
        headers = self._get_headers()

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            # Create sorted query string for signature (no URL encoding for signature)
            sorted_params = sorted(params.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            signature = self._generate_signature(query_string)
            # URL-encode the query string for the actual request
            encoded_query = urlencode(sorted_params)
            url = f"{self.base_url}{endpoint}?{encoded_query}&signature={signature}"
        else:
            url = f"{self.base_url}{endpoint}"
            if params:
                url += "?" + urlencode(params)

        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() == "POST":
                # POST with params in query string, empty body
                response = await self.client.post(url, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                error_msg = data.get("msg", "Unknown error")
                error_logger.error(f"API Error: {error_msg}")
                raise Exception(f"BingX API Error: {error_msg}")

            result: dict[str, Any] = data.get("data", data)
            return result

        except httpx.HTTPStatusError as e:
            error_logger.error(f"HTTP Error: {e}")
            raise
        except Exception as e:
            error_logger.error(f"Request Error: {e}")
            raise

    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        endpoint = "/openApi/swap/v2/quote/price"
        params = {"symbol": symbol}
        data = await self._request("GET", endpoint, params, signed=False)
        return float(data["price"])

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Get kline/candlestick data (cached for 60s).

        Args:
            symbol: Trading pair (e.g., "BTC-USDT")
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            limit: Number of klines to fetch (max 1000)

        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp
        """
        cache_key = f"klines:{symbol}:{interval}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return,unused-ignore]

        endpoint = "/openApi/swap/v2/quote/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        data = await self._request("GET", endpoint, params, signed=False)

        df = pd.DataFrame(
            data,
            columns=["timestamp", "open", "high", "low", "close", "volume", "close_time"],
        )
        df = df.astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            }
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        self._set_cache(cache_key, df)
        return df

    async def get_balance(self) -> dict[str, Any]:
        """Get account balance (cached for 30s)."""
        cached = self._get_cached("balance")
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        endpoint = "/openApi/swap/v2/user/balance"
        data = await self._request("GET", endpoint)

        self._set_cache("balance", data)
        return data

    async def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get open positions (cached for 15s)."""
        cache_key = f"positions:{symbol or 'all'}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        endpoint = "/openApi/swap/v2/user/positions"
        params: dict[str, str] = {}
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", endpoint, params)
        result: list[dict[str, Any]] = data if isinstance(data, list) else []

        self._set_cache(cache_key, result)
        return result

    async def get_open_orders(self, symbol: str) -> list[dict[str, Any]]:
        """Get open orders for a symbol (cached for 15s)."""
        cache_key = f"open_orders:{symbol}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        endpoint = "/openApi/swap/v2/trade/openOrders"
        params = {"symbol": symbol}
        data = await self._request("GET", endpoint, params)
        result: list[dict[str, Any]] = data.get("orders", []) if isinstance(data, dict) else data

        self._set_cache(cache_key, result)
        return result

    async def create_order(
        self,
        symbol: str,
        side: str,
        position_side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        take_profit: dict | None = None,
        stop_loss: dict | None = None,
    ) -> dict:
        """
        Create a new order.

        Args:
            symbol: Trading pair (e.g., "BTC-USDT")
            side: "BUY" or "SELL"
            position_side: "LONG" or "SHORT"
            order_type: "MARKET", "LIMIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"
            quantity: Order quantity
            price: Limit price (required for LIMIT orders)
            stop_price: Stop/trigger price (for STOP orders)
            take_profit: Take profit settings {"type": str, "stopPrice": float}
            stop_loss: Stop loss settings {"type": str, "stopPrice": float}

        Returns:
            Order response with orderId
        """
        endpoint = "/openApi/swap/v2/trade/order"
        params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": order_type,
            "quantity": quantity,
            "clientOrderID": str(uuid.uuid4()),  # Required for VST demo
        }

        if price is not None:
            params["price"] = price

        if stop_price is not None:
            params["stopPrice"] = stop_price

        if take_profit:
            params["takeProfit"] = json.dumps(take_profit, separators=(",", ":"))

        if stop_loss:
            params["stopLoss"] = json.dumps(stop_loss, separators=(",", ":"))

        try:
            data = await self._request("POST", endpoint, params)

            # Invalidate cache after order creation
            self._invalidate_cache("open_orders", "positions", "balance")

            # Only log success if we get a valid response with orderId
            order_id = data.get("orderId") or data.get("order", {}).get("orderId")
            if order_id:
                orders_logger.info(
                    f"Order created: {side} {position_side} {quantity} {symbol} @ {price or 'MARKET'} | ID: {order_id}"
                )
            else:
                orders_logger.warning(f"Order response missing orderId: {data}")

            return data
        except Exception as e:
            orders_logger.error(
                f"FAILED to create order: {side} {position_side} {quantity} {symbol} @ {price or 'MARKET'} | Error: {e}"
            )
            raise

    async def create_limit_order_with_tp(
        self,
        symbol: str,
        side: str,
        position_side: str,
        price: float,
        quantity: float,
        tp_price: float,
    ) -> dict:
        """
        Create a LIMIT order with embedded take profit.

        Args:
            symbol: Trading pair
            side: "BUY" or "SELL"
            position_side: "LONG" or "SHORT"
            price: Entry price
            quantity: Order quantity
            tp_price: Take profit price

        Returns:
            Order response
        """
        take_profit = {
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": tp_price,
            "price": tp_price,
            "workingType": "MARK_PRICE",
        }

        return await self.create_order(
            symbol=symbol,
            side=side,
            position_side=position_side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            take_profit=take_profit,
        )

    async def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancel an open order."""
        endpoint = "/openApi/swap/v2/trade/order"
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        data = await self._request("DELETE", endpoint, params)

        # Invalidate cache after cancellation
        self._invalidate_cache("open_orders", "positions", "balance")

        orders_logger.info(f"Order cancelled: {order_id}")
        return data

    async def cancel_all_orders(self, symbol: str) -> dict:
        """Cancel all open orders for a symbol."""
        endpoint = "/openApi/swap/v2/trade/allOpenOrders"
        params = {"symbol": symbol}
        data = await self._request("DELETE", endpoint, params)

        # Invalidate cache after cancellation
        self._invalidate_cache("open_orders", "positions", "balance")

        orders_logger.info(f"All orders cancelled for {symbol}")
        return data

    async def modify_tp_order(
        self,
        symbol: str,
        old_tp_order_id: str,
        side: str,
        position_side: str,
        quantity: float,
        new_tp_price: float,
    ) -> dict:
        """
        Modify a take profit order by canceling the old one and creating a new one.

        Since BingX doesn't have a native "modify order" endpoint, this method
        implements the modify operation as:
        1. Cancel the existing TP order
        2. Create a new TP order with the updated price

        Args:
            symbol: Trading symbol (e.g., "BTC-USDT")
            old_tp_order_id: Order ID of the existing TP order to be canceled
            side: "BUY" or "SELL" (opposite of position side for TP)
            position_side: "LONG" or "SHORT"
            quantity: Order quantity (must match position quantity)
            new_tp_price: New take profit price

        Returns:
            dict with new order details including:
                - order: New TP order response from create_order
                - oldOrderId: The canceled order ID
                - newOrderId: The new TP order ID

        Raises:
            Exception: If cancellation fails or new order creation fails

        Note:
            This is an atomic-like operation. If the cancellation succeeds but
            the new order creation fails, you may end up without TP protection.
            The caller should handle this scenario appropriately.
        """
        try:
            # Step 1: Cancel the old TP order
            await self.cancel_order(symbol, old_tp_order_id)
            orders_logger.info(
                f"Old TP order canceled: {old_tp_order_id[:8]} " f"(${new_tp_price:,.2f})"
            )

            # Step 2: Create new TP order with updated price
            new_tp_order = await self.create_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                order_type="TAKE_PROFIT_MARKET",
                quantity=quantity,
                stop_price=new_tp_price,
            )

            new_order_id = new_tp_order["data"]["order"]["orderId"]
            orders_logger.info(
                f"New TP order created: {new_order_id[:8]} " f"at ${new_tp_price:,.2f}"
            )

            # Invalidate cache after modification
            self._invalidate_cache("open_orders", "positions")

            return {
                "order": new_tp_order,
                "oldOrderId": old_tp_order_id,
                "newOrderId": new_order_id,
            }

        except Exception as e:
            error_logger.error(f"Failed to modify TP order {old_tp_order_id[:8]}: {e}")
            raise

    async def set_leverage(self, symbol: str, leverage: int, side: str = "BOTH") -> dict:
        """Set leverage for a symbol."""
        endpoint = "/openApi/swap/v2/trade/leverage"
        params = {
            "symbol": symbol,
            "leverage": leverage,
            "side": side,
        }
        return await self._request("POST", endpoint, params)

    async def set_margin_mode(self, symbol: str, margin_type: str) -> dict:
        """
        Set margin mode for a symbol.

        Args:
            symbol: Trading symbol (e.g., BTC-USDT)
            margin_type: CROSSED or ISOLATED

        Returns:
            API response dict

        Note:
            Cannot change margin mode when positions are open.
        """
        endpoint = "/openApi/swap/v2/trade/marginType"
        params = {
            "symbol": symbol,
            "marginType": margin_type,
        }
        return await self._request("POST", endpoint, params)

    async def get_margin_mode(self, symbol: str) -> str:
        """
        Get current margin mode for a symbol.

        Args:
            symbol: Trading symbol (e.g., BTC-USDT)

        Returns:
            Current margin mode: CROSSED or ISOLATED
        """
        # Get position info which includes margin mode
        positions = await self.get_positions(symbol)

        # If no positions, return CROSSED as default (BingX default)
        if not positions:
            return "CROSSED"

        # Return margin type from first position
        margin_type = positions[0].get("marginType", "CROSSED")
        return str(margin_type)

    async def get_funding_rate(self, symbol: str) -> dict[str, Any]:
        """
        Get current funding rate for a symbol (cached for 5 min).

        Returns:
            dict with:
                - lastFundingRate: Current funding rate (e.g., 0.0001 = 0.01%)
                - nextFundingTime: Timestamp of next funding settlement
                - markPrice: Current mark price
        """
        cache_key = f"funding_rate:{symbol}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        endpoint = "/openApi/swap/v2/quote/premiumIndex"
        params = {"symbol": symbol}
        data = await self._request("GET", endpoint, params, signed=False)

        result = {
            "symbol": symbol,
            "lastFundingRate": float(data.get("lastFundingRate", 0)),
            "nextFundingTime": int(data.get("nextFundingTime", 0)),
            "markPrice": float(data.get("markPrice", 0)),
        }

        self._set_cache(cache_key, result)
        return result

    async def generate_listen_key(self) -> str:
        """Generate a listenKey for WebSocket account updates."""
        endpoint = "/openApi/user/auth/userDataStream"
        # This endpoint returns listenKey directly, not wrapped in "data"
        params = {"timestamp": int(time.time() * 1000)}
        query_string = f"timestamp={params['timestamp']}"
        signature = self._generate_signature(query_string)

        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        headers = self._get_headers()

        try:
            response = await self.client.post(url, headers=headers)
            data = response.json()

            if response.status_code != 200:
                error_logger.error(f"ListenKey API error: {response.status_code} - {data}")
                return ""

            listen_key: str = data.get("listenKey", "")
            if not listen_key:
                error_logger.error(f"ListenKey vazio na resposta: {data}")
            return listen_key
        except Exception as e:
            error_logger.error(f"Erro ao gerar listenKey: {e}")
            return ""

    async def keep_alive_listen_key(self, listen_key: str) -> bool:
        """Keep listenKey alive (call every 30 minutes)."""
        endpoint = "/openApi/user/auth/userDataStream"
        params = {"listenKey": listen_key, "timestamp": int(time.time() * 1000)}
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        signature = self._generate_signature(query_string)

        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        headers = self._get_headers()

        response = await self.client.put(url, headers=headers)
        return bool(response.status_code == 200)

    async def close_listen_key(self, listen_key: str) -> bool:
        """Close/invalidate a listenKey."""
        endpoint = "/openApi/user/auth/userDataStream"
        params = {"listenKey": listen_key, "timestamp": int(time.time() * 1000)}
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        signature = self._generate_signature(query_string)

        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        headers = self._get_headers()

        response = await self.client.delete(url, headers=headers)
        return bool(response.status_code == 200)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
