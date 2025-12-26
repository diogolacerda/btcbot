"""
Tests for BUG-002 fixes.

Tests:
1. MACD calculation handles overflow gracefully
2. Dashboard calculations handle extreme values
3. WebSocket configuration doesn't use conflicting ping settings
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from config import MACDConfig
from src.grid.order_tracker import OrderStatus, TrackedOrder, TradeRecord
from src.strategy.macd_strategy import MACDStrategy
from src.ui.dashboard import Dashboard


class TestMACDOverflowFix:
    """Test MACD calculation overflow protection."""

    def test_macd_with_extreme_values(self):
        """Test MACD calculation with extreme price values."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)

        # Create klines with extreme values that would cause overflow
        extreme_prices = [1e15] * 100  # Extremely large prices
        klines = pd.DataFrame(
            {
                "close": extreme_prices,
                "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="1h"),
            }
        )

        # Should not raise overflow error, should return None or valid values
        result = strategy.calculate_macd(klines)

        # Either returns None (skipped due to extreme values) or returns valid values
        if result is not None:
            assert not np.isnan(result.macd_line), "MACD line should not be NaN"
            assert not np.isinf(result.macd_line), "MACD line should not be infinite"
            assert abs(result.macd_line) < 1e10, "MACD line should be clamped"

    def test_macd_with_null_values(self):
        """Test MACD calculation with null values."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)

        # Create klines with null values
        prices = [100.0] * 50 + [None] * 50
        klines = pd.DataFrame(
            {
                "close": prices,
                "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="1h"),
            }
        )

        # Should return None due to null values
        result = strategy.calculate_macd(klines)
        assert result is None, "Should return None for klines with null values"

    def test_macd_with_negative_prices(self):
        """Test MACD calculation with negative prices."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)

        # Create klines with negative prices (invalid)
        prices = [-100.0] * 100
        klines = pd.DataFrame(
            {
                "close": prices,
                "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="1h"),
            }
        )

        # Should return None due to negative prices
        result = strategy.calculate_macd(klines)
        assert result is None, "Should return None for negative prices"

    def test_macd_with_normal_values(self):
        """Test MACD calculation with normal BTC prices."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)

        # Create klines with normal BTC prices
        prices = [95000.0 + i * 10 for i in range(100)]  # Trending prices
        klines = pd.DataFrame(
            {
                "close": prices,
                "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="1h"),
            }
        )

        # Should successfully calculate MACD
        result = strategy.calculate_macd(klines)
        assert result is not None, "Should calculate MACD for normal prices"
        assert isinstance(result.macd_line, float), "MACD line should be a float"
        assert isinstance(result.histogram, float), "Histogram should be a float"


class TestDashboardOverflowFix:
    """Test dashboard calculation overflow protection."""

    def test_dashboard_positions_with_extreme_values(self):
        """Test dashboard positions table with extreme price values."""
        dashboard = Dashboard()

        # Create a position with extreme values
        position = TrackedOrder(
            order_id="test123",
            entry_price=1e15,  # Extreme price
            tp_price=1e15 * 1.01,
            quantity=0.001,
            status=OrderStatus.FILLED,
            filled_at=datetime.now(),
        )

        current_price = 1e15

        # Should not raise overflow error
        try:
            panel = dashboard.create_positions_table([position], current_price)
            assert panel is not None, "Should create panel without error"
        except OverflowError:
            pytest.fail("Dashboard should not raise overflow error")

    def test_dashboard_history_with_extreme_pnl(self):
        """Test dashboard history table with extreme PnL values."""
        dashboard = Dashboard()

        # Create a trade with values that could cause overflow
        trade = TradeRecord(
            entry_price=100000.0,
            exit_price=100001.0,
            quantity=1e10,  # Extreme quantity
            pnl=1e15,  # Extreme PnL
            entry_time=datetime.now(),
            exit_time=datetime.now(),
        )

        # Should not raise overflow error
        try:
            panel = dashboard.create_history_table([trade])
            assert panel is not None, "Should create panel without error"
        except (OverflowError, ZeroDivisionError):
            pytest.fail("Dashboard should handle extreme values gracefully")

    def test_dashboard_normal_values(self):
        """Test dashboard with normal trading values."""
        dashboard = Dashboard()

        # Create a position with normal values
        position = TrackedOrder(
            order_id="test123",
            entry_price=95000.0,
            tp_price=95500.0,
            quantity=0.001,
            status=OrderStatus.FILLED,
            filled_at=datetime.now(),
        )

        current_price = 95250.0

        # Should create panel successfully
        panel = dashboard.create_positions_table([position], current_price)
        assert panel is not None, "Should create panel for normal values"


class TestWebSocketConfiguration:
    """Test WebSocket ping/pong configuration."""

    def test_websocket_ping_disabled(self):
        """Verify that WebSocket library ping is disabled in favor of server ping."""
        # This is a code verification test - checking the configuration
        with open("/Users/diogolacerda/Sites/btcbot/src/client/websocket_client.py") as f:
            content = f.read()

        # Should use None for ping_interval to disable library ping
        assert "ping_interval=None" in content, "WebSocket should disable library ping"
        assert "ping_timeout=None" in content, "WebSocket should disable library ping timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
