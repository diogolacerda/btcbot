"""Tests for dynamic order limit based on filled orders awaiting TP (BE-008).

Note: The count is based on TP orders, not exchange positions, because
BingX consolidates multiple fills into one position but keeps separate TPs.
"""

import pytest

from config import GridAnchorMode, GridConfig, SpacingType
from src.grid.grid_calculator import GridCalculator


class TestDynamicOrderLimit:
    """Test dynamic order limit calculation based on filled orders (TP count)."""

    @pytest.fixture
    def config(self):
        """Create config with max_total_orders=10."""
        return GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,
            range_percent=5,
            take_profit_percent=1.0,
            max_total_orders=10,
            anchor_mode=GridAnchorMode.NONE,
            anchor_value=100,
        )

    @pytest.fixture
    def config_anchored(self):
        """Create config with anchoring enabled."""
        return GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,
            range_percent=5,
            take_profit_percent=1.0,
            max_total_orders=10,
            anchor_mode=GridAnchorMode.HUNDRED,
            anchor_value=100,
        )

    def test_no_filled_orders_full_slots(self, config):
        """With 0 filled orders (TPs), all slots available for LIMIT orders."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        filled_orders_count = 0  # No TPs = no filled orders

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Should create up to max_total_orders
        assert len(levels) == 10

    def test_some_filled_orders_reduced_slots(self, config):
        """With 3 filled orders (TPs), only 7 slots available."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        filled_orders_count = 3  # 3 TPs = 3 filled orders awaiting TP

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Should create max_total_orders - filled = 10 - 3 = 7
        assert len(levels) == 7

    def test_max_filled_orders_no_slots(self, config):
        """With max_total_orders filled orders (TPs), no slots available."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        filled_orders_count = 10  # 10 TPs = all slots used

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Should create 0 orders
        assert len(levels) == 0

    def test_filled_orders_plus_limit_orders_at_limit(self, config):
        """Filled orders + existing LIMIT orders should respect total limit."""
        calculator = GridCalculator(config)
        current_price = 88050

        # 3 existing LIMIT orders
        existing_orders = [
            {"orderId": "1", "price": "87900", "type": "LIMIT"},
            {"orderId": "2", "price": "87800", "type": "LIMIT"},
            {"orderId": "3", "price": "87700", "type": "LIMIT"},
        ]
        # 5 filled orders (5 TPs awaiting execution)
        filled_orders_count = 5

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Available: max_total_orders - filled - existing_orders = 10 - 5 - 3 = 2
        assert len(levels) == 2

    def test_exceeds_limit_no_new_orders(self, config):
        """If filled orders + LIMIT orders >= limit, no new orders."""
        calculator = GridCalculator(config)
        current_price = 88050

        # 5 existing LIMIT orders
        existing_orders = [
            {"orderId": f"{i}", "price": f"{87900 - i * 100}", "type": "LIMIT"} for i in range(5)
        ]
        # 6 filled orders (total = 11, exceeds limit of 10)
        filled_orders_count = 6

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Available: max(0, 10 - 6 - 5) = max(0, -1) = 0
        assert len(levels) == 0

    def test_cancel_excess_orders_with_filled_orders(self, config_anchored):
        """Should cancel excess LIMIT orders when filled orders reduce available slots."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # 8 existing LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(8)
        ]
        # 5 filled orders (total = 13, available limit slots = 10 - 5 = 5)
        filled_orders_count = 5

        orders_to_cancel = calculator.get_orders_to_cancel(
            current_price, existing_orders, filled_orders_count
        )

        # Should cancel 3 orders (8 existing - 5 available slots = 3 to cancel)
        assert len(orders_to_cancel) == 3

    def test_cancel_orders_with_max_filled_orders(self, config_anchored):
        """With max filled orders, all LIMIT orders should be cancelled."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # 5 existing LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(5)
        ]
        # 10 filled orders (no slots available for LIMIT)
        filled_orders_count = 10

        orders_to_cancel = calculator.get_orders_to_cancel(
            current_price, existing_orders, filled_orders_count
        )

        # Should cancel all 5 LIMIT orders
        assert len(orders_to_cancel) == 5

    def test_summary_includes_filled_orders(self, config):
        """Grid summary should include filled orders count and available slots."""
        calculator = GridCalculator(config)
        current_price = 88050
        filled_orders_count = 3

        summary = calculator.get_grid_summary(current_price, filled_orders_count)

        assert summary["max_total_orders"] == 10
        assert summary["open_positions"] == 3  # Field name kept for backward compat
        assert summary["available_slots"] == 7

    def test_summary_with_max_filled_orders(self, config):
        """Grid summary should show 0 available slots when at max filled orders."""
        calculator = GridCalculator(config)
        current_price = 88050
        filled_orders_count = 10

        summary = calculator.get_grid_summary(current_price, filled_orders_count)

        assert summary["max_total_orders"] == 10
        assert summary["open_positions"] == 10  # Field name kept for backward compat
        assert summary["available_slots"] == 0

    def test_filled_orders_exceeding_max(self, config):
        """Edge case: filled orders can exceed max_total_orders (shouldn't break)."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        # More filled orders than max_total_orders (edge case)
        filled_orders_count = 15

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Should gracefully handle with 0 levels
        assert len(levels) == 0

        summary = calculator.get_grid_summary(current_price, filled_orders_count)
        assert summary["available_slots"] == 0


class TestDynamicOrderLimitIntegration:
    """Integration tests simulating real scenarios with TP-based counting."""

    @pytest.fixture
    def config(self):
        """Create config with max_total_orders=10."""
        return GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,
            range_percent=5,
            take_profit_percent=1.0,
            max_total_orders=10,
            anchor_mode=GridAnchorMode.HUNDRED,
            anchor_value=100,
        )

    def test_order_filled_reduces_available_slots(self, config):
        """When an order is filled (TP created), available slots should decrease."""
        calculator = GridCalculator(config)
        current_price = 88050

        # Initially: 0 filled (no TPs), 5 LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(5)
        ]
        filled_orders_count = 0  # No TPs yet

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 0 - 5 = 5
        assert len(levels_before) == 5

        # Order at 88000 gets filled (TP created)
        # Remove from LIMIT orders, increment filled count (TP added)
        existing_orders = [o for o in existing_orders if o["price"] != "88000"]
        filled_orders_count = 1  # 1 TP now exists

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 1 - 4 = 5 (same number but different reason)
        assert len(levels_after) == 5

    def test_tp_hit_increases_available_slots(self, config):
        """When TP is hit, filled order closes and available slots increase."""
        calculator = GridCalculator(config)
        current_price = 88050

        # State: 3 filled orders (3 TPs), 4 LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(87600 - i * 100), "type": "LIMIT"}
            for i in range(4)
        ]
        filled_orders_count = 3  # 3 TPs awaiting execution

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 3 - 4 = 3
        assert len(levels_before) == 3

        # One TP executes (filled order closed)
        filled_orders_count = 2  # Now only 2 TPs

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 2 - 4 = 4
        assert len(levels_after) == 4

    def test_all_tps_hit_full_slots_available(self, config):
        """When all TPs are hit, full slots become available."""
        calculator = GridCalculator(config)
        current_price = 88050

        # State: 10 filled orders (10 TPs), no LIMIT orders
        existing_orders: list[dict] = []
        filled_orders_count = 10  # All slots used by filled orders

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 10 - 0 = 0
        assert len(levels_before) == 0

        # All TPs hit (all filled orders closed)
        filled_orders_count = 0

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )
        # Available: 10 - 0 - 0 = 10
        assert len(levels_after) == 10

    def test_bingx_consolidated_position_scenario(self, config):
        """
        Test the BingX-specific scenario where multiple fills are consolidated.

        BingX consolidates 11 filled orders into 1 position, but keeps 11 TPs.
        The old code would count 1 position, allowing overflow.
        The new code counts 11 TPs, correctly blocking new orders.
        """
        calculator = GridCalculator(config)
        current_price = 88050

        # Scenario: 11 orders were filled over time
        # BingX shows 1 consolidated position, but 11 TPs exist
        # Old behavior: count = 1 (wrong!)
        # New behavior: count = 11 (correct!)
        filled_orders_count = 11  # Count TPs, not positions

        # Also have 7 LIMIT orders pending
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(87400 - i * 100), "type": "LIMIT"}
            for i in range(7)
        ]

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, filled_orders_count
        )

        # Available: max(0, 10 - 11 - 7) = max(0, -8) = 0
        # No new orders should be created (overflow detected!)
        assert len(levels) == 0
