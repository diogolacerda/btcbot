"""Tests for dynamic order limit based on open positions (BE-008)."""

import pytest

from config import GridAnchorMode, GridConfig, SpacingType
from src.grid.grid_calculator import GridCalculator


class TestDynamicOrderLimit:
    """Test dynamic order limit calculation based on open positions."""

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

    def test_no_positions_full_slots(self, config):
        """With 0 positions, all slots available for LIMIT orders."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        open_positions_count = 0

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Should create up to max_total_orders
        assert len(levels) == 10

    def test_some_positions_reduced_slots(self, config):
        """With 3 positions, only 7 slots available."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        open_positions_count = 3

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Should create max_total_orders - positions = 10 - 3 = 7
        assert len(levels) == 7

    def test_all_positions_no_slots(self, config):
        """With max_total_orders positions, no slots available."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        open_positions_count = 10

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Should create 0 orders
        assert len(levels) == 0

    def test_positions_plus_orders_at_limit(self, config):
        """Positions + existing orders should respect total limit."""
        calculator = GridCalculator(config)
        current_price = 88050

        # 3 existing LIMIT orders
        existing_orders = [
            {"orderId": "1", "price": "87900", "type": "LIMIT"},
            {"orderId": "2", "price": "87800", "type": "LIMIT"},
            {"orderId": "3", "price": "87700", "type": "LIMIT"},
        ]
        # 5 open positions
        open_positions_count = 5

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Available: max_total_orders - positions - existing_orders = 10 - 5 - 3 = 2
        assert len(levels) == 2

    def test_exceeds_limit_no_new_orders(self, config):
        """If positions + orders >= limit, no new orders."""
        calculator = GridCalculator(config)
        current_price = 88050

        # 5 existing LIMIT orders
        existing_orders = [
            {"orderId": f"{i}", "price": f"{87900 - i * 100}", "type": "LIMIT"} for i in range(5)
        ]
        # 6 open positions (total = 11, exceeds limit of 10)
        open_positions_count = 6

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Available: max(0, 10 - 6 - 5) = max(0, -1) = 0
        assert len(levels) == 0

    def test_cancel_excess_orders_with_positions(self, config_anchored):
        """Should cancel excess LIMIT orders when positions reduce available slots."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # 8 existing LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(8)
        ]
        # 5 open positions (total = 13, available limit slots = 10 - 5 = 5)
        open_positions_count = 5

        orders_to_cancel = calculator.get_orders_to_cancel(
            current_price, existing_orders, open_positions_count
        )

        # Should cancel 3 orders (8 existing - 5 available slots = 3 to cancel)
        assert len(orders_to_cancel) == 3

    def test_cancel_orders_with_max_positions(self, config_anchored):
        """With max positions, all LIMIT orders should be cancelled."""
        calculator = GridCalculator(config_anchored)
        current_price = 88500

        # 5 existing LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(5)
        ]
        # 10 open positions (no slots available for LIMIT)
        open_positions_count = 10

        orders_to_cancel = calculator.get_orders_to_cancel(
            current_price, existing_orders, open_positions_count
        )

        # Should cancel all 5 LIMIT orders
        assert len(orders_to_cancel) == 5

    def test_summary_includes_positions(self, config):
        """Grid summary should include position count and available slots."""
        calculator = GridCalculator(config)
        current_price = 88050
        open_positions_count = 3

        summary = calculator.get_grid_summary(current_price, open_positions_count)

        assert summary["max_total_orders"] == 10
        assert summary["open_positions"] == 3
        assert summary["available_slots"] == 7

    def test_summary_with_max_positions(self, config):
        """Grid summary should show 0 available slots when at max positions."""
        calculator = GridCalculator(config)
        current_price = 88050
        open_positions_count = 10

        summary = calculator.get_grid_summary(current_price, open_positions_count)

        assert summary["max_total_orders"] == 10
        assert summary["open_positions"] == 10
        assert summary["available_slots"] == 0

    def test_positions_exceeding_max(self, config):
        """Edge case: positions can exceed max_total_orders (shouldn't break)."""
        calculator = GridCalculator(config)
        current_price = 88050

        existing_orders: list[dict] = []
        # More positions than max_total_orders (edge case)
        open_positions_count = 15

        levels = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )

        # Should gracefully handle with 0 levels
        assert len(levels) == 0

        summary = calculator.get_grid_summary(current_price, open_positions_count)
        assert summary["available_slots"] == 0


class TestDynamicOrderLimitIntegration:
    """Integration tests simulating real scenarios."""

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
        """When an order is filled, available slots should decrease."""
        calculator = GridCalculator(config)
        current_price = 88050

        # Initially: 0 positions, 5 LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(88000 - i * 100), "type": "LIMIT"}
            for i in range(5)
        ]
        open_positions_count = 0

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 0 - 5 = 5
        assert len(levels_before) == 5

        # Order at 88000 gets filled (becomes position)
        # Remove from orders, add to positions
        existing_orders = [o for o in existing_orders if o["price"] != "88000"]
        open_positions_count = 1

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 1 - 4 = 5 (same number but different reason)
        assert len(levels_after) == 5

    def test_tp_hit_increases_available_slots(self, config):
        """When TP is hit, position closes and available slots increase."""
        calculator = GridCalculator(config)
        current_price = 88050

        # State: 3 positions, 4 LIMIT orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(87600 - i * 100), "type": "LIMIT"}
            for i in range(4)
        ]
        open_positions_count = 3

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 3 - 4 = 3
        assert len(levels_before) == 3

        # One position closes (TP hit)
        open_positions_count = 2

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 2 - 4 = 4
        assert len(levels_after) == 4

    def test_all_tps_hit_full_slots_available(self, config):
        """When all TPs are hit, full slots become available."""
        calculator = GridCalculator(config)
        current_price = 88050

        # State: 10 positions (max), no LIMIT orders
        existing_orders: list[dict] = []
        open_positions_count = 10

        levels_before = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 10 - 0 = 0
        assert len(levels_before) == 0

        # All TPs hit
        open_positions_count = 0

        levels_after = calculator.get_levels_to_create(
            current_price, existing_orders, open_positions_count
        )
        # Available: 10 - 0 - 0 = 10
        assert len(levels_after) == 10
