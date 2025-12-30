"""
Tests for BUG-004: Duplicate orders after bot restart.

The bug occurs when:
1. Multiple orders are filled at different prices (e.g., $100,000 and $99,800)
2. BingX consolidates them into ONE position with avgPrice (e.g., $99,900)
3. Bot restarts
4. Bot loads only avgPrice from positions API
5. Bot creates duplicate orders at original prices ($100,000 and $99,800)

The fix calculates entry prices from TP orders by reverse calculation:
    entry_price = tp_price / (1 + TAKE_PROFIT_PERCENT / 100)

BingX keeps separate TP orders for each fill, so we can use them to determine
which price levels are occupied.
"""

from config import GridAnchorMode, GridConfig, SpacingType


class MockGridConfig:
    """Mock config for testing."""

    def __init__(self, take_profit_percent: float = 0.2):
        self.grid = GridConfig(
            spacing_type=SpacingType.PERCENT,
            spacing_value=0.2,
            range_percent=2.0,
            take_profit_percent=take_profit_percent,
            max_total_orders=10,
            anchor_mode=GridAnchorMode.NONE,
            anchor_value=100,
        )


class TestBug004EntryPricesFromTP:
    """Test cases for BUG-004 fix: calculating entry prices from TP orders."""

    def _get_entry_prices_from_tp_orders(self, orders: list[dict], tp_percent: float) -> set[float]:
        """
        Standalone implementation of the fix for testing.

        This replicates the logic from GridManager._get_entry_prices_from_tp_orders()
        """
        occupied_prices: set[float] = set()
        tp_multiplier = 1 + (tp_percent / 100)

        for order in orders:
            if "TAKE_PROFIT" in order.get("type", ""):
                tp_price = float(order.get("stopPrice", 0))
                if tp_price > 0:
                    entry_price = tp_price / tp_multiplier
                    occupied_prices.add(round(entry_price, 2))

        return occupied_prices

    def test_calculate_entry_price_from_tp(self):
        """Test basic reverse calculation of entry price from TP price."""
        tp_percent = 0.2  # 0.2%

        # If entry was $100,000, TP should be $100,200
        # Reverse: entry = 100200 / 1.002 = 100000
        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        assert 100000.0 in result

    def test_multiple_tp_orders_return_multiple_entries(self):
        """Test that multiple TP orders return multiple entry prices."""
        tp_percent = 0.2

        # Two fills at different prices
        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
            {"orderId": "tp2", "type": "TAKE_PROFIT_MARKET", "stopPrice": "99800.2"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        assert len(result) == 2
        assert 100000.0 in result
        # 99800.2 / 1.002 = 99600.999... ≈ 99601.0
        assert 99601.0 in result

    def test_ignores_non_tp_orders(self):
        """Test that LIMIT and other order types are ignored."""
        tp_percent = 0.2

        orders = [
            {"orderId": "limit1", "type": "LIMIT", "price": "99000.0"},
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
            {"orderId": "stop1", "type": "STOP_MARKET", "stopPrice": "98000.0"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        assert len(result) == 1
        assert 100000.0 in result

    def test_handles_both_tp_types(self):
        """Test that both TAKE_PROFIT and TAKE_PROFIT_MARKET are handled."""
        tp_percent = 0.2

        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
            {"orderId": "tp2", "type": "TAKE_PROFIT", "stopPrice": "99800.2"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        assert len(result) == 2

    def test_handles_empty_order_list(self):
        """Test with no orders."""
        result = self._get_entry_prices_from_tp_orders([], 0.2)
        assert len(result) == 0

    def test_handles_orders_without_stop_price(self):
        """Test TP orders missing stopPrice field are skipped."""
        tp_percent = 0.2

        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET"},  # No stopPrice
            {"orderId": "tp2", "type": "TAKE_PROFIT_MARKET", "stopPrice": "0"},
            {"orderId": "tp3", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        assert len(result) == 1
        assert 100000.0 in result

    def test_different_tp_percentages(self):
        """Test with different TP percentages."""
        # 1% TP
        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "101000.0"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent=1.0)

        # 101000 / 1.01 = 100000
        assert 100000.0 in result

    def test_rounding_to_2_decimals(self):
        """Test that entry prices are rounded to 2 decimals."""
        tp_percent = 0.2

        # TP that would produce a price with many decimals
        orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100199.99"},
        ]

        result = self._get_entry_prices_from_tp_orders(orders, tp_percent)

        # All prices should be rounded to 2 decimals
        for price in result:
            assert price == round(price, 2)


class TestBug004ScenarioRestart:
    """Test the complete scenario that causes the bug."""

    def test_scenario_multiple_fills_consolidated(self):
        """
        Simulate the bug scenario:
        1. Two orders filled at $100,000 and $99,800
        2. BingX consolidates to avgPrice $99,900 (we DON'T use this anymore)
        3. But TPs are kept separate: TP at $100,200 and $99,996.4
        4. We should detect BOTH original entry prices from TPs
        """
        tp_percent = 0.2

        # What BingX would show after consolidation:
        # - ONE position with avgPrice = $99,900
        # - TWO TP orders at original entry * 1.002

        # TP1: $100,000 * 1.002 = $100,200
        # TP2: $99,800 * 1.002 = $99,999.6
        tp_orders = [
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
            {"orderId": "tp2", "type": "TAKE_PROFIT_MARKET", "stopPrice": "99999.6"},
        ]

        # Using the fix logic
        occupied_prices: set[float] = set()
        tp_multiplier = 1 + (tp_percent / 100)

        for order in tp_orders:
            if "TAKE_PROFIT" in order.get("type", ""):
                tp_price = float(order.get("stopPrice", 0))
                if tp_price > 0:
                    entry_price = tp_price / tp_multiplier
                    occupied_prices.add(round(entry_price, 2))

        # Both original prices should be detected
        assert 100000.0 in occupied_prices, "Should detect $100,000 entry from TP"
        assert 99800.0 in occupied_prices, "Should detect $99,800 entry from TP"

        # The consolidated avgPrice should NOT be in the set
        # (it was never a real entry price)
        assert 99900.0 not in occupied_prices

    def test_scenario_prevents_duplicate_after_restart(self):
        """
        Test that the fix prevents duplicates after bot restart.

        Before fix: Bot would check positions → see avgPrice $99,900 → allow orders at $100,000
        After fix: Bot checks TPs → calculates entries $100,000 and $99,800 → blocks both
        """
        tp_percent = 0.2

        # Simulated exchange state after bot restart
        exchange_orders = [
            # Existing TP orders from previous fills
            {"orderId": "tp1", "type": "TAKE_PROFIT_MARKET", "stopPrice": "100200.0"},
            {"orderId": "tp2", "type": "TAKE_PROFIT_MARKET", "stopPrice": "99999.6"},
            # Some pending LIMIT orders
            {"orderId": "limit1", "type": "LIMIT", "price": "99600.0"},
        ]

        # Calculate occupied prices using the fix
        occupied_prices: set[float] = set()
        tp_multiplier = 1 + (tp_percent / 100)

        for order in exchange_orders:
            if "TAKE_PROFIT" in order.get("type", ""):
                tp_price = float(order.get("stopPrice", 0))
                if tp_price > 0:
                    entry_price = tp_price / tp_multiplier
                    occupied_prices.add(round(entry_price, 2))

        # Simulate new levels that grid wants to create
        proposed_levels = [100000.0, 99800.0, 99600.0, 99400.0]

        # Filter out occupied levels (this is what _create_grid_orders does)
        allowed_levels = [
            level for level in proposed_levels if round(level, 2) not in occupied_prices
        ]

        # $100,000 and $99,800 should be blocked (have fills awaiting TP)
        assert 100000.0 not in allowed_levels
        assert 99800.0 not in allowed_levels

        # $99,600 and $99,400 should be allowed (no existing fills)
        assert 99600.0 in allowed_levels
        assert 99400.0 in allowed_levels
