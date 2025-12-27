"""Tests for grid anchoring functionality (BE-021)."""

import pytest

from config import GridAnchorMode, GridConfig, SpacingType
from src.grid.grid_calculator import GridCalculator
from src.utils.helpers import anchor_price


class TestAnchorPrice:
    """Test the anchor_price helper function."""

    def test_anchor_to_hundreds(self):
        """Test anchoring to hundreds."""
        assert anchor_price(88050, 100) == 88000.0
        assert anchor_price(87932.5, 100) == 87900.0
        assert anchor_price(88150, 100) == 88100.0
        assert anchor_price(88199.99, 100) == 88100.0

    def test_anchor_exact_level(self):
        """Test anchoring when price is exactly at anchor level."""
        assert anchor_price(88000, 100) == 88000.0
        assert anchor_price(87900, 100) == 87900.0

    def test_anchor_to_thousands(self):
        """Test anchoring to thousands."""
        assert anchor_price(88050, 1000) == 88000.0
        assert anchor_price(87932.5, 1000) == 87000.0
        assert anchor_price(92500, 1000) == 92000.0

    def test_anchor_zero_value(self):
        """Test that zero anchor value returns original price."""
        assert anchor_price(88050, 0) == 88050

    def test_anchor_negative_value(self):
        """Test that negative anchor value returns original price."""
        assert anchor_price(88050, -100) == 88050


class TestGridCalculatorAnchored:
    """Test GridCalculator with anchoring enabled."""

    @pytest.fixture
    def config_anchored(self):
        """Create config with anchoring enabled."""
        return GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,  # Not used in anchored mode
            range_percent=5,
            take_profit_percent=1.0,
            max_orders=10,
            anchor_mode=GridAnchorMode.HUNDRED,
            anchor_value=100,
        )

    @pytest.fixture
    def config_normal(self):
        """Create config with anchoring disabled."""
        return GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,
            range_percent=5,
            take_profit_percent=1.0,
            max_orders=10,
            anchor_mode=GridAnchorMode.NONE,
            anchor_value=100,
        )

    def test_get_anchor_level(self, config_anchored):
        """Test get_anchor_level method."""
        calculator = GridCalculator(config_anchored)

        assert calculator.get_anchor_level(88050) == 88000.0
        assert calculator.get_anchor_level(87932.5) == 87900.0
        assert calculator.get_anchor_level(88150) == 88100.0

    def test_get_anchor_level_disabled(self, config_normal):
        """Test get_anchor_level when anchoring is disabled."""
        calculator = GridCalculator(config_normal)

        # Should return original price
        assert calculator.get_anchor_level(88050) == 88050
        assert calculator.get_anchor_level(87932.5) == 87932.5

    def test_calculate_levels_anchored(self, config_anchored):
        """Test that levels are created at anchor points."""
        calculator = GridCalculator(config_anchored)
        current_price = 88050  # Between 88000 and 88100

        levels = calculator.calculate_levels(current_price)

        # Should create orders at: 88000, 87900, 87800, etc
        assert len(levels) == 10  # max_orders

        # Check first few levels are at anchor points
        assert levels[0].entry_price == 88000.0
        assert levels[1].entry_price == 87900.0
        assert levels[2].entry_price == 87800.0
        assert levels[3].entry_price == 87700.0

        # All prices should be multiples of 100
        for level in levels:
            assert level.entry_price % 100 == 0

    def test_calculate_levels_price_at_anchor(self, config_anchored):
        """Test level calculation when price is exactly at anchor level."""
        calculator = GridCalculator(config_anchored)
        current_price = 88000  # Exactly at anchor

        levels = calculator.calculate_levels(current_price)

        # Should start from the level below (87900)
        assert len(levels) > 0
        assert levels[0].entry_price == 87900.0
        assert levels[1].entry_price == 87800.0

    def test_calculate_levels_normal_mode(self, config_normal):
        """Test that normal mode still works with spacing."""
        calculator = GridCalculator(config_normal)
        current_price = 88050

        levels = calculator.calculate_levels(current_price)

        # Should create orders with regular spacing
        assert len(levels) == 10

        # First level should be current_price - spacing
        expected_first = 88050 - 100
        assert abs(levels[0].entry_price - expected_first) < 1

    def test_get_orders_to_cancel_anchored_excess(self, config_anchored):
        """Test that excess orders are cancelled in anchored mode."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # Simulate 12 existing orders (2 more than max_orders)
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(12)
        ]

        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # Should cancel the 2 furthest orders (lowest prices)
        assert len(orders_to_cancel) == 2
        # Orders are sorted by price (descending), so after taking first 10, we cancel the last 2
        # The 12 orders are at: 88000, 87900, ..., 86900, 86800 (0-1100 offsets)
        # Last 2 are at indexes 10 and 11: 87000 and 86900
        cancelled_prices = sorted([float(o["price"]) for o in orders_to_cancel])
        assert cancelled_prices == [86900, 87000]

    def test_get_orders_to_cancel_anchored_within_limit(self, config_anchored):
        """Test that no orders are cancelled when within limit."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # Simulate 8 existing orders (within max_orders)
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(8)
        ]

        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # Should not cancel any orders
        assert len(orders_to_cancel) == 0

    def test_get_orders_to_cancel_outside_range(self, config_anchored):
        """Test that orders outside range are cancelled."""
        calculator = GridCalculator(config_anchored)
        current_price = 90000

        # min_price = 90000 * 0.95 = 85500
        # Create orders with some below min_price
        existing_orders = [
            {"orderId": "order_1", "price": "89000", "type": "LIMIT"},
            {"orderId": "order_2", "price": "88000", "type": "LIMIT"},
            {"orderId": "order_3", "price": "85000", "type": "LIMIT"},  # Below min_price
            {"orderId": "order_4", "price": "84000", "type": "LIMIT"},  # Below min_price
        ]

        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # Should cancel orders below min_price
        assert len(orders_to_cancel) >= 2
        cancelled_prices = [float(o["price"]) for o in orders_to_cancel]
        assert 85000 in cancelled_prices
        assert 84000 in cancelled_prices

    def test_get_orders_to_cancel_ignores_tp_orders(self, config_anchored):
        """Test that TP orders are not cancelled."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # Mix of LIMIT and TP orders
        existing_orders = [
            {"orderId": "order_1", "price": "88000", "type": "LIMIT"},
            {"orderId": "tp_1", "price": "89000", "type": "TAKE_PROFIT_MARKET"},
            {"orderId": "order_2", "price": "87900", "type": "LIMIT"},
            {"orderId": "tp_2", "price": "88900", "type": "TAKE_PROFIT_MARKET"},
        ]

        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # Should only consider LIMIT orders
        for order in orders_to_cancel:
            assert order["type"] == "LIMIT"

    def test_price_rising_scenario(self, config_anchored):
        """Test realistic scenario of price rising."""
        calculator = GridCalculator(config_anchored)

        # Initial state: price at 88050
        current_price = 88050
        levels = calculator.calculate_levels(current_price)

        # Should have orders at: 88000, 87900, ..., 87100
        initial_prices = [level.entry_price for level in levels]
        assert initial_prices[0] == 88000.0
        assert initial_prices[-1] == 87100.0

        # Price rises to 88150
        current_price = 88150

        # Existing orders (simulate the initial 10)
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(price), "type": "LIMIT"}
            for i, price in enumerate(initial_prices)
        ]

        # First, check what to cancel
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # With 10 existing orders and max_orders=10, AND a new anchor level (88100) available,
        # should cancel the furthest order (87100) to make room
        # min_price = 88150 * 0.95 = 83742.5, so all current orders (87100+) are in range
        assert len(orders_to_cancel) == 1
        assert float(orders_to_cancel[0]["price"]) == 87100.0

        # Calculate new levels (excluding existing)
        existing_prices = [float(o["price"]) for o in existing_orders]
        new_levels = calculator.calculate_levels(current_price, existing_prices)

        # Should create new order at 88100 (the new anchor level below price)
        # But we already have 10 orders, so we need to check if there's room
        # Since no orders were cancelled, there's no room for new orders
        # So new_levels should be empty OR we need to manually cancel one first
        # Let's check: with existing_prices containing 10 items, get_levels_to_create
        # should return empty because we're at max capacity

        # Actually, the test should simulate the manager's behavior:
        # 1. Cancel furthest orders if we need room
        # 2. Then create new ones

        # So let's manually simulate: we want 88100, so we need to cancel 87100
        # But get_orders_to_cancel doesn't do this automatically - it only cancels
        # orders that exceed max_orders OR are outside range

        # The grid "floats" by the manager creating new orders and cancelling old ones
        # Let's verify that new levels includes 88100
        new_level_prices = [level.entry_price for level in new_levels]
        assert 88100.0 in new_level_prices

    def test_price_descending_scenario(self, config_anchored):
        """Test that price descending doesn't cancel orders."""
        calculator = GridCalculator(config_anchored)

        # Initial state: price at 88050
        current_price = 88050

        # Price drops to 87500
        current_price = 87500

        # Simulate some orders were filled (removed from list)
        existing_orders = [
            {"orderId": "order_1", "price": "87900", "type": "LIMIT"},
            {"orderId": "order_2", "price": "87800", "type": "LIMIT"},
            {"orderId": "order_3", "price": "87700", "type": "LIMIT"},
        ]

        # Should be able to create more orders below
        existing_prices = [float(o["price"]) for o in existing_orders]
        new_levels = calculator.calculate_levels(current_price, existing_prices)

        # Should create new levels at: 87400, 87300, etc (avoiding existing)
        assert len(new_levels) > 0
        new_prices = [level.entry_price for level in new_levels]
        assert 87400.0 in new_prices

        # No orders should be cancelled
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)
        assert len(orders_to_cancel) == 0
