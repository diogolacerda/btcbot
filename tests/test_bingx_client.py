"""
Tests for BingXClient.modify_tp_order method (BE-042).

Tests the modify_tp_order functionality which cancels an existing TP order
and creates a new one with an updated price.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from config import BingXConfig
from src.client.bingx_client import BingXClient


@pytest.fixture
def bingx_config():
    """Create a test BingX configuration."""
    return BingXConfig(
        api_key="test_api_key",  # pragma: allowlist secret
        secret_key="test_secret_key",  # pragma: allowlist secret
        is_demo=False,
    )


@pytest.fixture
def client(bingx_config):
    """Create a BingXClient instance with test config."""
    return BingXClient(bingx_config)


class TestModifyTPOrder:
    """Test BingXClient.modify_tp_order method."""

    @pytest.mark.asyncio
    async def test_modify_tp_order_success(self, client):
        """Test successful TP order modification."""
        # Mock cancel_order to simulate successful cancellation
        client.cancel_order = AsyncMock(return_value={"code": 0, "msg": "Success", "data": {}})

        # Mock create_order to simulate successful new TP order creation
        mock_new_order_response = {
            "orderId": "new_tp_order_123",
        }
        client.create_order = AsyncMock(return_value=mock_new_order_response)

        # Execute modify_tp_order
        result = await client.modify_tp_order(
            symbol="BTC-USDT",
            old_tp_order_id="old_tp_order_789",
            side="SELL",
            position_side="LONG",
            quantity=0.001,
            new_tp_price=105000.0,
        )

        # Verify cancel_order was called with correct params
        client.cancel_order.assert_called_once_with("BTC-USDT", "old_tp_order_789")

        # Verify create_order was called with correct params
        client.create_order.assert_called_once_with(
            symbol="BTC-USDT",
            side="SELL",
            position_side="LONG",
            order_type="TAKE_PROFIT_MARKET",
            quantity=0.001,
            stop_price=105000.0,
        )

        # Verify returned result structure
        assert "order" in result
        assert "oldOrderId" in result
        assert "newOrderId" in result
        assert result["oldOrderId"] == "old_tp_order_789"
        assert result["newOrderId"] == "new_tp_order_123"
        assert result["order"] == mock_new_order_response

    @pytest.mark.asyncio
    async def test_modify_tp_order_cancel_failure(self, client):
        """Test TP order modification when cancellation fails."""
        # Mock cancel_order to simulate failure
        client.cancel_order = AsyncMock(side_effect=Exception("Failed to cancel order"))

        # Execute modify_tp_order and expect exception
        with pytest.raises(Exception, match="Failed to cancel order"):
            await client.modify_tp_order(
                symbol="BTC-USDT",
                old_tp_order_id="old_tp_order_789",
                side="SELL",
                position_side="LONG",
                quantity=0.001,
                new_tp_price=105000.0,
            )

        # Verify cancel_order was called
        client.cancel_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_tp_order_create_failure(self, client):
        """Test TP order modification when new order creation fails."""
        # Mock cancel_order to simulate successful cancellation
        client.cancel_order = AsyncMock(return_value={"code": 0, "msg": "Success", "data": {}})

        # Mock create_order to simulate failure
        client.create_order = AsyncMock(side_effect=Exception("Failed to create new TP order"))

        # Execute modify_tp_order and expect exception
        with pytest.raises(Exception, match="Failed to create new TP order"):
            await client.modify_tp_order(
                symbol="BTC-USDT",
                old_tp_order_id="old_tp_order_789",
                side="SELL",
                position_side="LONG",
                quantity=0.001,
                new_tp_price=105000.0,
            )

        # Verify both methods were called
        client.cancel_order.assert_called_once()
        client.create_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_tp_order_cache_invalidation(self, client):
        """Test that cache is invalidated after TP order modification."""
        # Mock cancel_order
        client.cancel_order = AsyncMock(return_value={"code": 0, "msg": "Success", "data": {}})

        # Mock create_order
        mock_new_order_response = {
            "orderId": "new_tp_order_123",
        }
        client.create_order = AsyncMock(return_value=mock_new_order_response)

        # Mock _invalidate_cache to track calls
        client._invalidate_cache = MagicMock()

        # Execute modify_tp_order
        await client.modify_tp_order(
            symbol="BTC-USDT",
            old_tp_order_id="old_tp_order_789",
            side="SELL",
            position_side="LONG",
            quantity=0.001,
            new_tp_price=105000.0,
        )

        # Verify cache invalidation was called with correct prefixes
        client._invalidate_cache.assert_called_once_with("open_orders", "positions")

    @pytest.mark.asyncio
    async def test_modify_tp_order_different_prices(self, client):
        """Test TP order modification with various price values."""
        # Mock cancel_order and create_order
        client.cancel_order = AsyncMock(return_value={"code": 0, "msg": "Success", "data": {}})
        client.create_order = AsyncMock(
            return_value={
                "orderId": "new_tp_order_123",
            }
        )

        # Test with different price values
        test_prices = [100000.0, 105000.5, 110250.25, 99999.99]

        for new_price in test_prices:
            await client.modify_tp_order(
                symbol="BTC-USDT",
                old_tp_order_id="old_tp_order_789",
                side="SELL",
                position_side="LONG",
                quantity=0.001,
                new_tp_price=new_price,
            )

            # Verify create_order was called with the correct new price
            _, kwargs = client.create_order.call_args
            assert kwargs["stop_price"] == new_price

    @pytest.mark.asyncio
    async def test_modify_tp_order_different_quantities(self, client):
        """Test TP order modification with various quantity values."""
        # Mock cancel_order and create_order
        client.cancel_order = AsyncMock(return_value={"code": 0, "msg": "Success", "data": {}})
        client.create_order = AsyncMock(
            return_value={
                "orderId": "new_tp_order_123",
            }
        )

        # Test with different quantity values
        test_quantities = [0.001, 0.01, 0.1, 1.0]

        for qty in test_quantities:
            await client.modify_tp_order(
                symbol="BTC-USDT",
                old_tp_order_id="old_tp_order_789",
                side="SELL",
                position_side="LONG",
                quantity=qty,
                new_tp_price=105000.0,
            )

            # Verify create_order was called with the correct quantity
            _, kwargs = client.create_order.call_args
            assert kwargs["quantity"] == qty
