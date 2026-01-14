"""
Tests for BUG-004: Cancel orders when filter passes to NEGATIVE state.

Validates that LIMIT orders are cancelled ONLY when:
1. MACD state transitions from ACTIVE/ACTIVATE to PAUSE/INACTIVE/WAIT
2. Filter is ENABLED via API AND indicator is already in negative state (PAUSE/WAIT/INACTIVE)

IMPORTANT: Orders are NOT cancelled when:
- Filter is DISABLED (disabling = ignoring filter, can continue operating)
- Filter is ENABLED but indicator is in positive state (ACTIVE/ACTIVATE)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from src.grid.grid_manager import GridManager
from src.strategy.macd_strategy import GridState


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.trading = MagicMock()
    config.trading.symbol = "BTC-USDT"
    config.trading.order_size_usdt = 100
    config.trading.leverage = 10
    config.macd = MagicMock()
    config.macd.fast = 12
    config.macd.slow = 26
    config.macd.signal = 9
    config.macd.timeframe = "15m"
    config.grid = MagicMock()
    config.grid.take_profit_percent = 0.5
    return config


@pytest.fixture
def mock_client():
    """Create a mock BingX client."""
    client = AsyncMock()
    client.set_leverage = AsyncMock()
    client.get_positions = AsyncMock(return_value=[])
    client.get_open_orders = AsyncMock(return_value=[])
    client.cancel_order = AsyncMock()
    client.get_price = AsyncMock(return_value=50000.0)
    client.get_klines = AsyncMock(return_value=pd.DataFrame({"close": [50000] * 100}))
    return client


@pytest.fixture
async def grid_manager(mock_config, mock_client):
    """Create a GridManager instance with mocked dependencies."""
    # Clear the singleton registry before each test
    from src.filters.registry import FilterRegistry

    registry = FilterRegistry()
    registry.clear()

    manager = GridManager(mock_config, mock_client)
    await manager.start()
    yield manager
    await manager.stop()

    # Clear again after test
    registry.clear()


@pytest.mark.asyncio
async def test_macd_state_change_active_to_pause_cancels_orders(grid_manager, mock_client):
    """Test that orders are cancelled when MACD transitions from ACTIVE to PAUSE."""
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "1", "type": "LIMIT", "price": 49000.0},
        {"orderId": "2", "type": "LIMIT", "price": 48000.0},
        {"orderId": "3", "type": "TAKE_PROFIT_MARKET", "price": 51000.0},  # Should NOT be cancelled
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Simulate MACD state change from ACTIVE to PAUSE
    grid_manager._macd_filter._current_state = GridState.ACTIVE
    await grid_manager._macd_filter.set_current_state(GridState.PAUSE)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify LIMIT orders were cancelled (2 calls)
    assert mock_client.cancel_order.call_count == 2
    mock_client.cancel_order.assert_any_call("BTC-USDT", "1")
    mock_client.cancel_order.assert_any_call("BTC-USDT", "2")


@pytest.mark.asyncio
async def test_macd_state_change_active_to_inactive_cancels_orders(grid_manager, mock_client):
    """Test that orders are cancelled when MACD transitions from ACTIVE to INACTIVE."""
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "10", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Simulate MACD state change from ACTIVE to INACTIVE
    grid_manager._macd_filter._current_state = GridState.ACTIVE
    await grid_manager._macd_filter.set_current_state(GridState.INACTIVE)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify order was cancelled
    assert mock_client.cancel_order.call_count == 1
    mock_client.cancel_order.assert_called_with("BTC-USDT", "10")


@pytest.mark.asyncio
async def test_macd_state_change_activate_to_wait_cancels_orders(grid_manager, mock_client):
    """Test that orders are cancelled when MACD transitions from ACTIVATE to WAIT."""
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "20", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Simulate MACD state change from ACTIVATE to WAIT
    grid_manager._macd_filter._current_state = GridState.ACTIVATE
    await grid_manager._macd_filter.set_current_state(GridState.WAIT)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify order was cancelled
    assert mock_client.cancel_order.call_count == 1


@pytest.mark.asyncio
async def test_macd_state_change_pause_to_active_does_not_cancel(grid_manager, mock_client):
    """Test that orders are NOT cancelled when MACD transitions from PAUSE to ACTIVE."""
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "30", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Simulate MACD state change from PAUSE to ACTIVE (should NOT cancel)
    grid_manager._macd_filter._current_state = GridState.PAUSE
    await grid_manager._macd_filter.set_current_state(GridState.ACTIVE)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_filter_disabled_via_api_does_not_cancel_orders(grid_manager, mock_client):
    """Test that orders are NOT cancelled when filter is disabled via API.

    Disabling a filter means ignoring it - the system can continue operating.
    """
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "40", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Disable filter via registry
    grid_manager._filter_registry.disable_filter("macd")

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled (disabling doesn't cancel)
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_filter_enabled_when_negative_cancels_orders(grid_manager, mock_client):
    """Test that orders are cancelled when filter is enabled AND indicator is in negative state."""
    # Setup: disable filter first
    grid_manager._filter_registry.disable_filter("macd")
    await asyncio.sleep(0.1)
    mock_client.cancel_order.reset_mock()

    # Setup: Set MACD to PAUSE (negative state)
    grid_manager._macd_filter._current_state = GridState.PAUSE

    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "50", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Enable filter via registry (should cancel because MACD is PAUSE)
    grid_manager._filter_registry.enable_filter("macd")

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify order was cancelled (enabled with negative state)
    assert mock_client.cancel_order.call_count == 1


@pytest.mark.asyncio
async def test_filter_enabled_when_positive_does_not_cancel(grid_manager, mock_client):
    """Test that orders are NOT cancelled when filter is enabled with indicator in positive state."""
    # Setup: Set MACD to ACTIVE (positive state) AND activate cycle and trigger
    grid_manager._macd_filter._current_state = GridState.ACTIVE
    grid_manager._macd_filter._strategy._cycle_activated = True  # Activate cycle
    grid_manager._macd_filter._strategy._trigger_activated = True  # Activate trigger (BE-029)

    # Setup: disable filter (state remains ACTIVE)
    grid_manager._filter_registry.disable_filter("macd")
    await asyncio.sleep(0.1)
    mock_client.cancel_order.reset_mock()

    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "51", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Enable filter via registry (should NOT cancel because MACD is ACTIVE and cycle activated)
    grid_manager._filter_registry.enable_filter("macd")

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled (positive state)
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_disable_all_filters_does_not_cancel_orders(grid_manager, mock_client):
    """Test that orders are NOT cancelled when all filters are disabled.

    Disabling filters means ignoring them - orders can continue.
    """
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "60", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Disable all filters
    grid_manager._filter_registry.disable_all()

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_enable_all_filters_when_negative_cancels_orders(grid_manager, mock_client):
    """Test that orders are cancelled when all filters enabled AND at least one is negative."""
    # Setup: disable all first
    grid_manager._filter_registry.disable_all()
    await asyncio.sleep(0.1)
    mock_client.cancel_order.reset_mock()

    # Setup: Set MACD to PAUSE (negative state)
    grid_manager._macd_filter._current_state = GridState.PAUSE

    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "70", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Enable all filters (should cancel because MACD is PAUSE)
    grid_manager._filter_registry.enable_all()

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify order was cancelled
    assert mock_client.cancel_order.call_count == 1


@pytest.mark.asyncio
async def test_enable_all_filters_when_positive_does_not_cancel(grid_manager, mock_client):
    """Test that orders are NOT cancelled when all filters enabled with positive state."""
    # Setup: Set MACD to ACTIVE (positive state) AND activate cycle and trigger
    grid_manager._macd_filter._current_state = GridState.ACTIVE
    grid_manager._macd_filter._strategy._cycle_activated = True  # Activate cycle
    grid_manager._macd_filter._strategy._trigger_activated = True  # Activate trigger (BE-029)

    # Setup: disable all (state remains ACTIVE)
    grid_manager._filter_registry.disable_all()
    await asyncio.sleep(0.1)
    mock_client.cancel_order.reset_mock()

    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "71", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Enable all filters (should NOT cancel because MACD is ACTIVE and cycle activated)
    grid_manager._filter_registry.enable_all()

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_take_profit_orders_are_preserved(grid_manager, mock_client):
    """Test that TAKE_PROFIT_MARKET orders are NOT cancelled."""
    # Setup: Start with ACTIVE state
    grid_manager._macd_filter._current_state = GridState.ACTIVE

    # Setup: create mix of orders
    mock_orders = [
        {"orderId": "80", "type": "LIMIT", "price": 49000.0},
        {"orderId": "81", "type": "TAKE_PROFIT_MARKET", "price": 51000.0},
        {"orderId": "82", "type": "STOP_MARKET", "price": 48000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Trigger MACD state change from ACTIVE to INACTIVE (should cancel LIMIT only)
    await grid_manager._macd_filter.set_current_state(GridState.INACTIVE)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify only LIMIT order was cancelled
    assert mock_client.cancel_order.call_count == 1
    mock_client.cancel_order.assert_called_with("BTC-USDT", "80")


@pytest.mark.asyncio
async def test_no_orders_does_not_fail(grid_manager, mock_client):
    """Test that cancellation with no open orders doesn't fail."""
    # Setup: Set MACD to PAUSE then INACTIVE to trigger cancellation
    grid_manager._macd_filter._current_state = GridState.PAUSE

    # Setup: no open orders
    mock_client.get_open_orders.return_value = []

    # Trigger MACD state change (should not fail even with no orders)
    await grid_manager._macd_filter.set_current_state(GridState.INACTIVE)

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify no errors and no cancel calls (no orders to cancel)
    assert mock_client.cancel_order.call_count == 0


@pytest.mark.asyncio
async def test_filter_state_unchanged_does_not_cancel(grid_manager, mock_client):
    """Test that no orders are cancelled if filter state doesn't actually change."""
    # Setup: create mock open orders
    mock_orders = [
        {"orderId": "90", "type": "LIMIT", "price": 49000.0},
    ]
    mock_client.get_open_orders.return_value = mock_orders

    # Try to enable already-enabled filter (no actual change)
    grid_manager._filter_registry.enable_filter("macd")

    # Wait for async task to complete
    await asyncio.sleep(0.1)

    # Verify NO orders were cancelled (state didn't change)
    assert mock_client.cancel_order.call_count == 0
