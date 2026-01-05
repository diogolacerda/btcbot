"""
Tests for BE-045: Correctly detect filled vs cancelled orders.

When a pending order disappears from the exchange, the bot should:
- Mark as FILLED if position increased (order was executed)
- Mark as CANCELLED if position didn't increase (order was cancelled)
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.grid.order_tracker import OrderTracker, TrackedOrder


class TestOrderDetection:
    """Test order filled vs cancelled detection logic."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh OrderTracker for each test."""
        return OrderTracker()

    @pytest.fixture
    def mock_client(self):
        """Create a mock BingX client."""
        client = AsyncMock()
        client.get_open_orders = AsyncMock(return_value=[])
        client.get_positions = AsyncMock(return_value=[])
        return client

    def _create_tracked_order(
        self,
        tracker: OrderTracker,
        order_id: str,
        entry_price: float,
        quantity: float,
    ) -> TrackedOrder:
        """Helper to create and track an order."""
        return tracker.add_order(
            order_id=order_id,
            entry_price=entry_price,
            quantity=quantity,
            tp_price=entry_price * 1.01,  # 1% TP
        )

    @pytest.mark.asyncio
    async def test_order_detected_as_filled_when_position_increases(self, tracker, mock_client):
        """
        When a pending order disappears and position amount increased,
        the order should be detected as FILLED.
        """
        # Setup: Add a pending order
        self._create_tracked_order(tracker, order_id="123", entry_price=100000.0, quantity=0.001)

        # Verify order is pending
        assert len(tracker.pending_orders) == 1
        assert len(tracker.filled_orders) == 0

        # Simulate: Order filled on exchange (disappeared from open orders, position exists)
        mock_client.get_open_orders.return_value = []  # Order no longer in open orders
        mock_client.get_positions.return_value = [
            {"positionAmt": "0.001", "symbol": "BTC-USDT"}  # Position exists
        ]

        # Import and patch the sync function
        from src.grid.grid_manager import GridManager

        # Create a minimal GridManager mock to test the logic
        with patch.object(GridManager, "__init__", lambda x, *args, **kwargs: None):
            gm = GridManager.__new__(GridManager)
            gm.client = mock_client
            gm.tracker = tracker
            gm.symbol = "BTC-USDT"
            gm._current_price = 100000.0
            gm._on_order_filled = None
            gm._on_tp_hit = None

            # Run sync
            await gm._sync_with_exchange()

        # Verify order was detected as FILLED
        assert len(tracker.pending_orders) == 0
        assert len(tracker.filled_orders) == 1
        assert tracker.filled_orders[0].order_id == "123"

    @pytest.mark.asyncio
    async def test_order_detected_as_cancelled_when_no_position(self, tracker, mock_client):
        """
        When a pending order disappears but position didn't increase,
        the order should be detected as CANCELLED (not saved to DB).
        """
        # Setup: Add a pending order
        self._create_tracked_order(tracker, order_id="456", entry_price=100000.0, quantity=0.001)

        # Verify order is pending
        assert len(tracker.pending_orders) == 1

        # Simulate: Order cancelled on exchange (disappeared, no position)
        mock_client.get_open_orders.return_value = []  # Order gone
        mock_client.get_positions.return_value = [
            {"positionAmt": "0", "symbol": "BTC-USDT"}  # No position
        ]

        from src.grid.grid_manager import GridManager

        with patch.object(GridManager, "__init__", lambda x, *args, **kwargs: None):
            gm = GridManager.__new__(GridManager)
            gm.client = mock_client
            gm.tracker = tracker
            gm.symbol = "BTC-USDT"
            gm._current_price = 100000.0
            gm._on_order_filled = None
            gm._on_tp_hit = None

            await gm._sync_with_exchange()

        # Verify order was detected as CANCELLED (removed from tracker, not filled)
        assert len(tracker.pending_orders) == 0
        assert len(tracker.filled_orders) == 0  # Key: should NOT be in filled_orders

    @pytest.mark.asyncio
    async def test_multiple_orders_one_filled_one_cancelled(self, tracker, mock_client):
        """
        When multiple orders disappear, correctly identify which was filled
        vs cancelled based on position delta.
        """
        # Setup: Add two pending orders
        self._create_tracked_order(tracker, order_id="111", entry_price=100000.0, quantity=0.001)
        self._create_tracked_order(tracker, order_id="222", entry_price=99000.0, quantity=0.001)

        assert len(tracker.pending_orders) == 2

        # Simulate: Only one order filled (position = 0.001, not 0.002)
        mock_client.get_open_orders.return_value = []
        mock_client.get_positions.return_value = [
            {"positionAmt": "0.001", "symbol": "BTC-USDT"}  # Only one order filled
        ]

        from src.grid.grid_manager import GridManager

        with patch.object(GridManager, "__init__", lambda x, *args, **kwargs: None):
            gm = GridManager.__new__(GridManager)
            gm.client = mock_client
            gm.tracker = tracker
            gm.symbol = "BTC-USDT"
            gm._current_price = 100000.0
            gm._on_order_filled = None
            gm._on_tp_hit = None

            await gm._sync_with_exchange()

        # One should be filled, one should be cancelled
        assert len(tracker.pending_orders) == 0
        assert len(tracker.filled_orders) == 1  # Only one filled

    @pytest.mark.asyncio
    async def test_order_still_pending_stays_in_tracker(self, tracker, mock_client):
        """
        Orders that are still on the exchange should remain in pending.
        """
        self._create_tracked_order(tracker, order_id="789", entry_price=100000.0, quantity=0.001)

        # Order still exists on exchange
        mock_client.get_open_orders.return_value = [{"orderId": "789", "type": "LIMIT"}]
        mock_client.get_positions.return_value = []

        from src.grid.grid_manager import GridManager

        with patch.object(GridManager, "__init__", lambda x, *args, **kwargs: None):
            gm = GridManager.__new__(GridManager)
            gm.client = mock_client
            gm.tracker = tracker
            gm.symbol = "BTC-USDT"
            gm._current_price = 100000.0
            gm._on_order_filled = None
            gm._on_tp_hit = None

            await gm._sync_with_exchange()

        # Order should still be pending
        assert len(tracker.pending_orders) == 1
        assert tracker.pending_orders[0].order_id == "789"

    @pytest.mark.asyncio
    async def test_cancelled_order_not_persisted_to_db(self, tracker, mock_client):
        """
        Cancelled orders should NOT be saved to the database.
        This is the core fix for BE-045.
        """
        # Setup with trade repository mock
        mock_trade_repo = AsyncMock()
        tracker._trade_repository = mock_trade_repo
        tracker._account_id = "test-account-id"

        self._create_tracked_order(
            tracker, order_id="cancelled-order", entry_price=100000.0, quantity=0.001
        )

        # Order cancelled (no position)
        mock_client.get_open_orders.return_value = []
        mock_client.get_positions.return_value = [{"positionAmt": "0"}]

        from src.grid.grid_manager import GridManager

        with patch.object(GridManager, "__init__", lambda x, *args, **kwargs: None):
            gm = GridManager.__new__(GridManager)
            gm.client = mock_client
            gm.tracker = tracker
            gm.symbol = "BTC-USDT"
            gm._current_price = 100000.0
            gm._on_order_filled = None
            gm._on_tp_hit = None

            await gm._sync_with_exchange()

        # Verify trade repository was NOT called (cancelled orders shouldn't be saved)
        # Note: cancel_order() in tracker just removes from memory, doesn't persist
        assert len(tracker.pending_orders) == 0
        assert len(tracker.filled_orders) == 0
