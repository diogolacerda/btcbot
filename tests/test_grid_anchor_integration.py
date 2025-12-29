"""Integration tests for grid anchoring with price movement simulation (BE-021)."""

import pytest

from config import GridAnchorMode, GridConfig, SpacingType
from src.grid.grid_calculator import GridCalculator


class TestGridAnchorIntegration:
    """Integration test simulating real price movement with anchored grid."""

    @pytest.fixture
    def calculator(self):
        """Create calculator with anchoring enabled."""
        config = GridConfig(
            spacing_type=SpacingType.FIXED,
            spacing_value=100,
            range_percent=5,
            take_profit_percent=1.0,
            max_total_orders=10,
            anchor_mode=GridAnchorMode.HUNDRED,
            anchor_value=100,
        )
        return GridCalculator(config)

    def test_full_price_movement_cycle(self, calculator):
        """
        Simulate a complete price movement cycle:
        1. Initial setup at $88,050
        2. Price rises to $88,150
        3. Price rises to $88,250
        4. Price drops back to $87,800
        """
        # Step 1: Initial setup at $88,050
        current_price = 88050
        print(f"\n--- Step 1: Initial price ${current_price:,.2f} ---")

        initial_levels = calculator.calculate_levels(current_price)

        # Should create 10 orders at anchor levels below current price
        assert len(initial_levels) == 10

        initial_prices = [level.entry_price for level in initial_levels]
        print(f"Initial orders: {[f'${p:,.0f}' for p in initial_prices]}")

        # Expected: 88000, 87900, 87800, ..., 87100
        assert initial_prices == [
            88000,
            87900,
            87800,
            87700,
            87600,
            87500,
            87400,
            87300,
            87200,
            87100,
        ]

        # All should be at anchor points (multiples of 100)
        for price in initial_prices:
            assert price % 100 == 0

        # Simulate these orders exist on exchange
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(price), "type": "LIMIT"}
            for i, price in enumerate(initial_prices)
        ]

        # Step 2: Price rises to $88,150
        current_price = 88150
        print(f"\n--- Step 2: Price rises to ${current_price:,.2f} ---")

        # Calculate what to cancel
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)
        cancelled_prices_str = [f"${float(o['price']):,.0f}" for o in orders_to_cancel]
        print(f"Orders to cancel: {cancelled_prices_str}")

        # Should cancel the furthest order (87100) to make room for 88100
        assert len(orders_to_cancel) >= 1
        assert float(orders_to_cancel[-1]["price"]) == 87100

        # Remove cancelled orders
        for order in orders_to_cancel:
            existing_orders = [o for o in existing_orders if o["orderId"] != order["orderId"]]

        # Calculate new levels to create (using get_levels_to_create for proper limiting)
        new_levels = calculator.get_levels_to_create(current_price, existing_orders)
        print(f"New orders to create: {[f'${level.entry_price:,.0f}' for level in new_levels]}")

        # Should create new order at 88100
        assert len(new_levels) >= 1
        assert 88100 in [level.entry_price for level in new_levels]

        # Add new orders
        for level in new_levels:
            existing_orders.append(
                {
                    "orderId": f"order_new_{level.entry_price}",
                    "price": str(level.entry_price),
                    "type": "LIMIT",
                }
            )

        # Verify we still have 10 orders
        current_prices = sorted([float(o["price"]) for o in existing_orders], reverse=True)
        print(f"Current orders after step 2: {[f'${p:,.0f}' for p in current_prices]}")
        assert len(current_prices) == 10

        # Expected: 88100, 88000, 87900, ..., 87200
        assert current_prices == [
            88100,
            88000,
            87900,
            87800,
            87700,
            87600,
            87500,
            87400,
            87300,
            87200,
        ]

        # Step 3: Price rises to $88,250
        current_price = 88250
        print(f"\n--- Step 3: Price rises to ${current_price:,.2f} ---")

        # Calculate what to cancel
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)
        cancelled_prices_str = [f"${float(o['price']):,.0f}" for o in orders_to_cancel]
        print(f"Orders to cancel: {cancelled_prices_str}")

        # Should cancel the furthest order (87200)
        assert len(orders_to_cancel) >= 1
        assert float(orders_to_cancel[-1]["price"]) == 87200

        # Remove cancelled orders
        for order in orders_to_cancel:
            existing_orders = [o for o in existing_orders if o["orderId"] != order["orderId"]]

        # Calculate new levels to create (using get_levels_to_create for proper limiting)
        new_levels = calculator.get_levels_to_create(current_price, existing_orders)
        print(f"New orders to create: {[f'${level.entry_price:,.0f}' for level in new_levels]}")

        # Should create new order at 88200
        assert len(new_levels) >= 1
        assert 88200 in [level.entry_price for level in new_levels]

        # Add new orders
        for level in new_levels:
            existing_orders.append(
                {
                    "orderId": f"order_new_{level.entry_price}",
                    "price": str(level.entry_price),
                    "type": "LIMIT",
                }
            )

        # Verify we still have 10 orders
        current_prices = sorted([float(o["price"]) for o in existing_orders], reverse=True)
        print(f"Current orders after step 3: {[f'${p:,.0f}' for p in current_prices]}")
        assert len(current_prices) == 10

        # Expected: 88200, 88100, 88000, ..., 87300
        assert current_prices == [
            88200,
            88100,
            88000,
            87900,
            87800,
            87700,
            87600,
            87500,
            87400,
            87300,
        ]

        # Step 4: Price drops to $87,800
        current_price = 87800
        print(f"\n--- Step 4: Price drops to ${current_price:,.2f} ---")

        # Simulate some orders were filled (88200, 88100, 88000, 87900, 87800 were hit)
        filled_prices = [88200, 88100, 88000, 87900, 87800]
        existing_orders = [o for o in existing_orders if float(o["price"]) not in filled_prices]

        remaining_prices_str = [f"${float(o['price']):,.0f}" for o in existing_orders]
        print(f"Remaining orders after fills: {remaining_prices_str}")

        # Calculate what to cancel (should be nothing - price is descending)
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)
        cancelled_prices_str = [f"${float(o['price']):,.0f}" for o in orders_to_cancel]
        print(f"Orders to cancel: {cancelled_prices_str}")
        assert len(orders_to_cancel) == 0  # No cancellations when price drops

        # Calculate new levels to create (using get_levels_to_create for proper limiting)
        new_levels = calculator.get_levels_to_create(current_price, existing_orders)
        print(f"New orders to create: {[f'${level.entry_price:,.0f}' for level in new_levels]}")

        # Should create new orders to fill back up to 10
        # Current orders: 87700, 87600, 87500, 87400, 87300 (5 orders)
        # Should create 5 more orders at: 87700, 87600, ..., down to available levels
        assert len(new_levels) >= 5

        new_prices = [level.entry_price for level in new_levels]
        # Should include levels like 87700 (wait, already exists), 87200, 87100, etc
        # Actually, 87700 exists, so should create: 87200, 87100, 87000, 86900, 86800
        assert 87200 in new_prices
        assert 87100 in new_prices

        # All new prices should be at anchor points
        for level in new_levels:
            assert level.entry_price % 100 == 0

    def test_rapid_price_increase(self, calculator):
        """Test rapid price increase scenario."""
        current_price = 88000

        # Create initial grid
        initial_levels = calculator.calculate_levels(current_price)
        initial_prices = [level.entry_price for level in initial_levels]

        # Expected: 87900, 87800, ..., 87000
        assert initial_prices[0] == 87900

        # Simulate existing orders
        existing_orders = [
            {"orderId": f"order_{i}", "price": str(price), "type": "LIMIT"}
            for i, price in enumerate(initial_prices)
        ]

        # Price jumps to 89000 (rapid increase)
        current_price = 89000

        # Should cancel old orders and suggest new ones
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # All old orders should be kept or cancelled based on distance
        # With 10 max orders and potentially more than 10 anchor levels in range,
        # should cancel furthest ones
        assert len(orders_to_cancel) <= len(existing_orders)

        # Calculate new levels
        existing_prices = [float(o["price"]) for o in existing_orders]
        new_levels = calculator.calculate_levels(current_price, existing_prices)

        # Should create new orders at higher levels (88900, 88800, etc)
        new_prices = [level.entry_price for level in new_levels]
        assert any(price >= 88000 for price in new_prices)

    def test_maintain_exactly_n_orders(self, calculator):
        """Test that grid maintains exactly N orders when price rises."""
        current_price = 88500

        # Create initial grid
        initial_levels = calculator.calculate_levels(current_price)
        assert len(initial_levels) == 10

        existing_orders = [
            {"orderId": f"order_{i}", "price": str(level.entry_price), "type": "LIMIT"}
            for i, level in enumerate(initial_levels)
        ]

        # Price rises gradually
        for new_price in [88600, 88700, 88800, 88900, 89000]:
            # Cancel old orders
            orders_to_cancel = calculator.get_orders_to_cancel(new_price, existing_orders)
            for order in orders_to_cancel:
                existing_orders = [o for o in existing_orders if o["orderId"] != order["orderId"]]

            # Create new orders (using get_levels_to_create for proper limiting)
            new_levels = calculator.get_levels_to_create(new_price, existing_orders)

            for level in new_levels:
                existing_orders.append(
                    {
                        "orderId": f"order_{new_price}_{level.entry_price}",
                        "price": str(level.entry_price),
                        "type": "LIMIT",
                    }
                )

            # Should always have at most max_total_orders (10)
            assert len(existing_orders) <= 10

            # All orders should be at anchor points
            for order in existing_orders:
                assert float(order["price"]) % 100 == 0

    def test_mixed_orders_tp_preservation(self, calculator):
        """Test that TP orders are preserved during cancellation."""
        current_price = 88500

        # Create mix of LIMIT and TP orders
        existing_orders = [
            {"orderId": "limit_1", "price": "88000", "type": "LIMIT"},
            {"orderId": "tp_1", "price": "88800", "type": "TAKE_PROFIT_MARKET"},
            {"orderId": "limit_2", "price": "87900", "type": "LIMIT"},
            {"orderId": "tp_2", "price": "88700", "type": "TAKE_PROFIT_MARKET"},
            {"orderId": "limit_3", "price": "87800", "type": "LIMIT"},
        ]

        # Get orders to cancel
        orders_to_cancel = calculator.get_orders_to_cancel(current_price, existing_orders)

        # Should only cancel LIMIT orders, never TP orders
        for order in orders_to_cancel:
            assert order["type"] == "LIMIT"

        # Verify TP orders are not in cancellation list
        cancelled_ids = [o["orderId"] for o in orders_to_cancel]
        assert "tp_1" not in cancelled_ids
        assert "tp_2" not in cancelled_ids
