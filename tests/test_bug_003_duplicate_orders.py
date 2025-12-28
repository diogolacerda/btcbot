"""
Tests for BUG-003: Bot creates duplicate order at same level before TP is hit.

The bug occurs when:
1. A limit order is filled (position opened)
2. TP order is placed but not yet hit
3. Bot creates another limit order at the same price

The fix adds a check for open positions on the exchange before creating new orders.
"""

from src.grid.order_tracker import OrderStatus, OrderTracker


class TestBug003DuplicateOrders:
    """Test cases for BUG-003 fix."""

    def test_tracker_keeps_filled_order_in_price_map(self):
        """Filled orders should remain in _orders_by_price to prevent duplicates."""
        tracker = OrderTracker()

        # Add a pending order
        tracker.add_order(
            order_id="order123",
            entry_price=88500.0,
            tp_price=88700.0,
            quantity=0.001,
        )

        # Verify it's tracked
        assert tracker.has_order_at_price(88500.0)
        assert tracker.get_order("order123").status == OrderStatus.PENDING

        # Mark as filled (order executed, position opened)
        tracker.order_filled("order123")

        # CRITICAL: Should still be in price map even after filled
        assert tracker.has_order_at_price(88500.0), (
            "Filled orders must remain in _orders_by_price "
            "to prevent duplicate orders at same price"
        )
        assert tracker.get_order("order123").status == OrderStatus.FILLED

    def test_tracker_removes_from_price_map_only_on_tp_hit(self):
        """Price should only be freed when TP is hit (position closed)."""
        tracker = OrderTracker()

        # Add and fill an order
        tracker.add_order(
            order_id="order123",
            entry_price=88500.0,
            tp_price=88700.0,
            quantity=0.001,
        )
        tracker.order_filled("order123")

        # Still blocked
        assert tracker.has_order_at_price(88500.0)

        # TP hit - position closed
        tracker.order_tp_hit("order123", exit_price=88700.0)

        # NOW the price should be freed
        assert not tracker.has_order_at_price(88500.0), "Price should be freed only after TP is hit"

    def test_tracker_blocks_duplicate_at_same_price(self):
        """Cannot add another order at price with existing pending/filled order."""
        tracker = OrderTracker()

        # Add first order
        tracker.add_order(
            order_id="order1",
            entry_price=88500.0,
            tp_price=88700.0,
            quantity=0.001,
        )

        # Check should return True (blocking duplicate creation)
        assert tracker.has_order_at_price(88500.0)

        # If we try to add another at same price, it would overwrite
        # This is the behavior we need to prevent in grid_manager
        # The fix in _create_grid_orders() checks has_order_at_price() before creating

    def test_position_price_blocking_scenario(self):
        """
        Simulate the bug scenario:
        1. Order at $88,500 is filled
        2. Position exists at $88,500
        3. Should NOT create another order at $88,500
        """
        tracker = OrderTracker()

        # Simulate filled order (position open, waiting for TP)
        tracker.add_order(
            order_id="order123",
            entry_price=88500.0,
            tp_price=88700.0,
            quantity=0.001,
        )
        tracker.order_filled("order123")

        # The grid_manager checks:
        # 1. has_order_at_price() - local tracker
        # 2. position_prices set - exchange positions
        # Both should block creation at this price

        assert tracker.has_order_at_price(
            88500.0
        ), "Tracker should block duplicate order at price with open position"

    def test_multiple_positions_partial_close(self):
        """
        When multiple positions exist and only one is closed,
        only that price should be freed.
        """
        tracker = OrderTracker()

        # Two positions at different prices
        tracker.add_order("order1", 88500.0, 88700.0, 0.001)
        tracker.add_order("order2", 88400.0, 88600.0, 0.001)
        tracker.order_filled("order1")
        tracker.order_filled("order2")

        # Both should be blocked
        assert tracker.has_order_at_price(88500.0)
        assert tracker.has_order_at_price(88400.0)

        # Close only first position
        tracker.order_tp_hit("order1", 88700.0)

        # First price freed, second still blocked
        assert not tracker.has_order_at_price(88500.0)
        assert tracker.has_order_at_price(88400.0)


class TestPositionPriceFiltering:
    """Test the position price filtering logic used in _create_grid_orders()."""

    def test_position_prices_set_creation(self):
        """Test building the position_prices set from exchange data."""
        # Simulate exchange positions response
        positions = [
            {"avgPrice": "88500.00", "positionAmt": "0.001"},
            {"avgPrice": "88400.00", "positionAmt": "0.002"},
            {"avgPrice": "0", "positionAmt": "0"},  # Empty position
        ]

        position_prices: set[float] = set()
        for pos in positions:
            avg_price = float(pos.get("avgPrice", 0))
            position_amt = float(pos.get("positionAmt", 0))
            if position_amt != 0 and avg_price > 0:
                position_prices.add(round(avg_price, 2))

        assert 88500.0 in position_prices
        assert 88400.0 in position_prices
        assert 0 not in position_prices
        assert len(position_prices) == 2

    def test_level_filtering_with_position_prices(self):
        """Test that levels are filtered when position exists at that price."""
        from dataclasses import dataclass

        @dataclass
        class MockLevel:
            entry_price: float

        # Levels to potentially create
        levels = [
            MockLevel(88500.0),
            MockLevel(88400.0),
            MockLevel(88300.0),
        ]

        # Position exists at 88500
        position_prices = {88500.0}

        # Filter levels (simulating _create_grid_orders logic)
        filtered = [level for level in levels if round(level.entry_price, 2) not in position_prices]

        # 88500 should be filtered out
        assert len(filtered) == 2
        assert all(level.entry_price != 88500.0 for level in filtered)

    def test_price_rounding_for_comparison(self):
        """Ensure price rounding works correctly for comparison."""
        # Exchange might return slightly different precision
        exchange_price = 88500.123456
        calculated_price = 88500.0

        # Both should match when rounded to 2 decimals
        rounded_exchange = round(exchange_price, 2)
        rounded_calculated = round(calculated_price, 2)

        assert rounded_exchange == 88500.12
        assert rounded_calculated == 88500.0
        # These don't match! That's why we round both consistently

        # With proper rounding
        position_prices = {round(exchange_price, 2)}
        should_block = round(calculated_price, 2) in position_prices

        # Different prices, so no block (correct behavior)
        assert not should_block

        # If prices are actually the same
        exchange_price_2 = 88500.001
        position_prices_2 = {round(exchange_price_2, 2)}  # {88500.0}
        should_block_2 = round(calculated_price, 2) in position_prices_2

        assert should_block_2, "Same price (when rounded) should block"
