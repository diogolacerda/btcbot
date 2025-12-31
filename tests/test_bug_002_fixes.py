"""
Tests for BUG-002 fixes.

Tests:
1. MACD calculation handles overflow gracefully
2. WebSocket configuration doesn't use conflicting ping settings
"""

import numpy as np
import pandas as pd
import pytest

from config import MACDConfig
from src.strategy.macd_strategy import MACDStrategy


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


class TestWebSocketConfiguration:
    """Test WebSocket ping/pong configuration."""

    def test_websocket_ping_disabled(self):
        """Verify that WebSocket library ping is disabled in favor of server ping."""
        # This is a code verification test - checking the configuration
        from pathlib import Path

        ws_file = Path(__file__).parent.parent / "src" / "client" / "websocket_client.py"
        with open(ws_file) as f:
            content = f.read()

        # Should use None for ping_interval to disable library ping
        assert "ping_interval=None" in content, "WebSocket should disable library ping"
        assert "ping_timeout=None" in content, "WebSocket should disable library ping timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
