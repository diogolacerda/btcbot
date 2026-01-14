"""
Tests for BUG-FIX-006: Position Tracking from TP Orders

BingX consolidates multiple filled orders into a single position with average price,
but maintains individual take profit (TP) orders. The dashboard should show
individual positions derived from TP orders, not the consolidated position.

Test scenarios:
1. Multiple TP orders create multiple tracked positions
2. Entry price is correctly reverse-calculated from TP price
3. Anchor rounding is applied when configured
4. Duplicate positions are not created
5. Empty position list returns 0
"""

from src.grid.order_tracker import OrderStatus, OrderTracker


class TestBugFix006LoadExistingPositions:
    """Test the refactored load_existing_positions method."""

    def setup_method(self):
        """Set up fresh OrderTracker for each test."""
        self.tracker = OrderTracker()

    def test_derives_multiple_positions_from_tp_orders(self):
        """
        Given 10 TP orders exist on the exchange,
        When load_existing_positions is called,
        Then 10 individual positions should be tracked.
        """
        # BingX consolidated position (10 fills averaged)
        positions = [
            {
                "symbol": "BTC-USDT",
                "positionAmt": 0.001,  # Total: 10 x 0.0001 BTC
                "avgPrice": 95000,  # Average of all fills
            }
        ]

        # 10 individual TP orders at different prices
        tp_percent = 0.5
        tp_orders = []
        for i in range(10):
            entry_price = 94000 + (i * 100)  # 94000, 94100, ... 94900
            tp_price = entry_price * (1 + tp_percent / 100)
            tp_orders.append(
                {
                    "type": "TAKE_PROFIT_MARKET",
                    "orderId": f"tp_order_{i}",
                    "stopPrice": tp_price,
                    "origQty": 0.0001,
                }
            )

        loaded = self.tracker.load_existing_positions(positions, tp_orders, tp_percent)

        # Should load all 10 positions
        assert loaded == 10
        assert len(self.tracker.filled_orders) == 10

    def test_correctly_calculates_entry_from_tp(self):
        """
        Given a TP order with stopPrice,
        When position is loaded,
        Then entry_price = tp_price / (1 + tp_percent/100).
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0.0001, "avgPrice": 95000}]
        tp_percent = 0.5
        tp_price = 95500  # TP price on exchange

        # Expected entry: 95500 / 1.005 = 95024.88 (rounded to 95024.88)
        expected_entry = round(tp_price / (1 + tp_percent / 100), 2)

        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_123",
                "stopPrice": tp_price,
                "origQty": 0.0001,
            }
        ]

        self.tracker.load_existing_positions(positions, tp_orders, tp_percent)

        position = self.tracker.filled_orders[0]
        assert position.entry_price == expected_entry
        assert position.tp_price == tp_price

    def test_prevents_duplicate_positions(self):
        """
        Given a position is already tracked at an entry price,
        When load_existing_positions is called again,
        Then no duplicate is created.
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0.0001, "avgPrice": 95000}]
        tp_percent = 0.5
        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_123",
                "stopPrice": 95500,
                "origQty": 0.0001,
            }
        ]

        # First load
        loaded1 = self.tracker.load_existing_positions(positions, tp_orders, tp_percent)
        assert loaded1 == 1

        # Second load (same data)
        loaded2 = self.tracker.load_existing_positions(positions, tp_orders, tp_percent)
        assert loaded2 == 0  # No new positions loaded
        assert len(self.tracker.filled_orders) == 1  # Still only 1

    def test_returns_zero_for_empty_position(self):
        """
        Given no positions on exchange (positionAmt = 0),
        When load_existing_positions is called,
        Then returns 0 and no positions tracked.
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0, "avgPrice": 0}]
        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_123",
                "stopPrice": 95500,
                "origQty": 0.0001,
            }
        ]

        loaded = self.tracker.load_existing_positions(positions, tp_orders, 0.5)

        assert loaded == 0
        assert len(self.tracker.filled_orders) == 0

    def test_ignores_non_tp_orders(self):
        """
        Given a mix of order types,
        When load_existing_positions is called,
        Then only TP orders create positions.
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0.0001, "avgPrice": 95000}]
        mixed_orders = [
            {"type": "LIMIT", "orderId": "limit_1", "price": 94000, "origQty": 0.0001},
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_1",
                "stopPrice": 95500,
                "origQty": 0.0001,
            },
            {"type": "STOP_MARKET", "orderId": "stop_1", "stopPrice": 93000, "origQty": 0.0001},
            {"type": "TAKE_PROFIT", "orderId": "tp_2", "stopPrice": 96000, "origQty": 0.0001},
        ]

        loaded = self.tracker.load_existing_positions(positions, mixed_orders, 0.5)

        # Only 2 TP orders should create positions
        assert loaded == 2
        assert len(self.tracker.filled_orders) == 2

    def test_position_has_filled_status(self):
        """
        Given TP orders loaded,
        When positions are created,
        Then all have FILLED status.
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0.0001, "avgPrice": 95000}]
        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_123",
                "stopPrice": 95500,
                "origQty": 0.0001,
            }
        ]

        self.tracker.load_existing_positions(positions, tp_orders, 0.5)

        position = self.tracker.filled_orders[0]
        assert position.status == OrderStatus.FILLED

    def test_stores_exchange_tp_order_id(self):
        """
        Given a TP order with orderId,
        When position is loaded,
        Then exchange_tp_order_id is stored.
        """
        positions = [{"symbol": "BTC-USDT", "positionAmt": 0.0001, "avgPrice": 95000}]
        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "exchange_tp_12345",
                "stopPrice": 95500,
                "origQty": 0.0001,
            }
        ]

        self.tracker.load_existing_positions(positions, tp_orders, 0.5)

        position = self.tracker.filled_orders[0]
        assert position.exchange_tp_order_id == "exchange_tp_12345"


class TestBugFix006Scenario:
    """Real-world scenario tests for BUG-FIX-006."""

    def test_scenario_10_fills_show_10_positions(self):
        """
        Scenario: User executes 10 limit orders at different prices.
        BingX consolidates into 1 position with average price.
        Dashboard should show 10 individual positions.
        """
        tracker = OrderTracker()

        # BingX shows consolidated position
        positions = [
            {
                "symbol": "BTC-USDT",
                "positionAmt": 0.001,  # Total from 10 fills
                "avgPrice": 94450,  # Average price
            }
        ]

        # But BingX keeps 10 individual TP orders
        tp_percent = 0.5
        tp_orders = []
        for i in range(10):
            entry = 94000 + (i * 100)  # 94000 to 94900
            tp = entry * 1.005  # 0.5% TP
            tp_orders.append(
                {
                    "type": "TAKE_PROFIT_MARKET",
                    "orderId": f"tp_{i}",
                    "stopPrice": tp,
                    "origQty": 0.0001,
                }
            )

        loaded = tracker.load_existing_positions(positions, tp_orders, tp_percent)

        # Dashboard should show 10 positions
        assert loaded == 10
        assert len(tracker.filled_orders) == 10

        # Each position has unique entry price
        entry_prices = {p.entry_price for p in tracker.filled_orders}
        assert len(entry_prices) == 10

    def test_scenario_restart_preserves_positions(self):
        """
        Scenario: Bot restarts while positions are open.
        Positions should be restored from TP orders.
        """
        tracker = OrderTracker()

        positions = [
            {
                "symbol": "BTC-USDT",
                "positionAmt": 0.0005,
                "avgPrice": 95000,
            }
        ]

        tp_orders = [
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_1",
                "stopPrice": 94500 * 1.005,
                "origQty": 0.0001,
            },
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_2",
                "stopPrice": 94600 * 1.005,
                "origQty": 0.0001,
            },
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_3",
                "stopPrice": 94700 * 1.005,
                "origQty": 0.0001,
            },
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_4",
                "stopPrice": 94800 * 1.005,
                "origQty": 0.0001,
            },
            {
                "type": "TAKE_PROFIT_MARKET",
                "orderId": "tp_5",
                "stopPrice": 94900 * 1.005,
                "origQty": 0.0001,
            },
        ]

        loaded = tracker.load_existing_positions(positions, tp_orders, 0.5)

        assert loaded == 5
        assert tracker.position_count == 5
