"""Tests for API schema serialization (BUG-002: Decimal formatting)."""

from datetime import datetime
from decimal import Decimal

from src.api.schemas.config import GridConfigResponse, TradingConfigResponse


class TestDecimalSerialization:
    """Test Decimal field serialization for consistent formatting."""

    def test_trading_config_normalizes_decimals(self):
        """Test that TradingConfigResponse normalizes Decimal values (BUG-002)."""
        # Create response with trailing zeros in Decimals
        config = TradingConfigResponse(
            id="test-id",
            account_id="test-account",
            symbol="BTC-USDT",
            leverage=10,
            order_size_usdt=Decimal("5.00"),  # Has trailing zeros
            margin_mode="CROSSED",
            take_profit_percent=Decimal("0.60"),  # Has trailing zero
            tp_dynamic_enabled=False,
            tp_base_percent=Decimal("0.50"),
            tp_min_percent=Decimal("0.30"),
            tp_max_percent=Decimal("1.00"),
            tp_safety_margin=Decimal("0.10"),
            tp_check_interval_min=60,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        # Serialize to dict (this uses field_serializer)
        data = config.model_dump(mode="json")

        # Assert normalized values (no trailing zeros)
        assert data["order_size_usdt"] == "5"
        assert data["take_profit_percent"] == "0.6"
        assert data["tp_base_percent"] == "0.5"
        assert data["tp_min_percent"] == "0.3"
        assert data["tp_max_percent"] == "1"
        assert data["tp_safety_margin"] == "0.1"

    def test_trading_config_preserves_precision(self):
        """Test that normalization doesn't lose precision."""
        config = TradingConfigResponse(
            id="test-id",
            account_id="test-account",
            symbol="BTC-USDT",
            leverage=10,
            order_size_usdt=Decimal("5.123"),  # Precise value
            margin_mode="CROSSED",
            take_profit_percent=Decimal("0.678"),  # Precise value
            tp_dynamic_enabled=False,
            tp_base_percent=Decimal("0.500"),
            tp_min_percent=Decimal("0.300"),
            tp_max_percent=Decimal("1.000"),
            tp_safety_margin=Decimal("0.100"),
            tp_check_interval_min=60,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        data = config.model_dump(mode="json")

        # Assert precision is preserved
        assert data["order_size_usdt"] == "5.123"
        assert data["take_profit_percent"] == "0.678"

    def test_grid_config_normalizes_decimals(self):
        """Test that GridConfigResponse normalizes Decimal values (BUG-002)."""
        config = GridConfigResponse(
            id="test-id",
            account_id="test-account",
            spacing_type="fixed",
            spacing_value=Decimal("100.00"),  # Has trailing zeros
            range_percent=Decimal("2.00"),  # Has trailing zeros
            max_total_orders=10,
            anchor_mode="hundred",
            anchor_value=Decimal("100.00"),  # Has trailing zeros
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        data = config.model_dump(mode="json")

        # Assert normalized values
        assert data["spacing_value"] == "100"
        assert data["range_percent"] == "2"
        assert data["anchor_value"] == "100"

    def test_grid_config_preserves_precision(self):
        """Test that normalization doesn't lose precision in grid config."""
        config = GridConfigResponse(
            id="test-id",
            account_id="test-account",
            spacing_type="percentage",
            spacing_value=Decimal("1.25"),  # Precise value
            range_percent=Decimal("2.5"),  # Precise value
            max_total_orders=10,
            anchor_mode="none",
            anchor_value=Decimal("50.75"),  # Precise value
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        data = config.model_dump(mode="json")

        # Assert precision is preserved
        assert data["spacing_value"] == "1.25"
        assert data["range_percent"] == "2.5"
        assert data["anchor_value"] == "50.75"

    def test_bug_002_reproduction(self):
        """Reproduce BUG-002: PATCH returns 0.60 instead of 0.6.

        This test validates the fix for the bug where
        take_profit_percent="0.6" returns as "0.60".
        """
        # Simulate PATCH input/output scenario from bug report
        config = TradingConfigResponse(
            id="test-id",
            account_id="test-account",
            symbol="BTC-USDT",
            leverage=10,
            order_size_usdt=Decimal("5.0"),
            margin_mode="CROSSED",
            take_profit_percent=Decimal("0.6"),  # Input from PATCH
            tp_dynamic_enabled=False,
            tp_base_percent=Decimal("0.5"),
            tp_min_percent=Decimal("0.3"),
            tp_max_percent=Decimal("1.0"),
            tp_safety_margin=Decimal("0.1"),
            tp_check_interval_min=60,
            created_at=datetime(2025, 1, 4, 0, 0, 0),
            updated_at=datetime(2025, 1, 4, 0, 0, 0),
        )

        data = config.model_dump(mode="json")

        # BUG-002: Before fix, this would be "0.60"
        # After fix, it should be "0.6" (normalized)
        assert data["take_profit_percent"] == "0.6", (
            f"BUG-002 not fixed: Expected normalized '0.6' but got '{data['take_profit_percent']}'"
        )
