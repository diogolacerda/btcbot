"""
Tests for DynamicTPManager (BE-007).

Tests:
1. Configuration validation
2. TP calculation based on funding rate
3. Position monitoring logic
4. Rate limiting for updates
5. Stats reporting
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from config import DynamicTPConfig
from src.grid.dynamic_tp_manager import DynamicTPManager, PositionTPUpdate
from src.grid.order_tracker import OrderStatus, TrackedOrder


class TestDynamicTPConfig:
    """Test DynamicTPConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DynamicTPConfig()

        assert config.enabled is False
        assert config.base_percent == 0.3
        assert config.min_percent == 0.3
        assert config.max_percent == 1.0
        assert config.safety_margin == 0.05
        assert config.check_interval_minutes == 60

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DynamicTPConfig(
            enabled=True,
            base_percent=0.5,
            min_percent=0.4,
            max_percent=2.0,
            safety_margin=0.1,
            check_interval_minutes=30,
        )

        assert config.enabled is True
        assert config.base_percent == 0.5
        assert config.min_percent == 0.4
        assert config.max_percent == 2.0
        assert config.safety_margin == 0.1
        assert config.check_interval_minutes == 30


class TestDynamicTPManagerBasic:
    """Test basic DynamicTPManager functionality."""

    def _create_manager(self, enabled: bool = True) -> DynamicTPManager:
        """Create a DynamicTPManager with mocks."""
        config = DynamicTPConfig(
            enabled=enabled,
            base_percent=0.3,
            min_percent=0.3,
            max_percent=1.0,
            safety_margin=0.05,
            check_interval_minutes=60,
        )
        client = MagicMock()
        order_tracker = MagicMock()
        return DynamicTPManager(config, client, order_tracker, "BTC-USDT")

    def test_is_enabled_true(self):
        """Test is_enabled property when enabled."""
        manager = self._create_manager(enabled=True)
        assert manager.is_enabled is True

    def test_is_enabled_false(self):
        """Test is_enabled property when disabled."""
        manager = self._create_manager(enabled=False)
        assert manager.is_enabled is False

    def test_start_when_disabled(self):
        """Test that start does nothing when disabled."""
        manager = self._create_manager(enabled=False)

        manager.start()

        assert manager._running is False
        assert manager._thread is None

    def test_start_when_enabled(self):
        """Test that start creates monitoring task when enabled."""
        manager = self._create_manager(enabled=True)

        manager.start()

        assert manager._running is True
        assert manager._thread is not None

        # Cleanup
        manager.stop()

    def test_stop(self):
        """Test that stop cancels monitoring task."""
        manager = self._create_manager(enabled=True)

        manager.start()
        assert manager._running is True

        manager.stop()
        assert manager._running is False
        assert manager._thread is None

    def test_double_start(self):
        """Test that starting twice doesn't create multiple tasks."""
        manager = self._create_manager(enabled=True)

        manager.start()
        thread1 = manager._thread

        manager.start()
        thread2 = manager._thread

        assert thread1 is thread2

        manager.stop()

    def test_double_stop(self):
        """Test that stopping twice doesn't cause issues."""
        manager = self._create_manager(enabled=True)

        manager.start()
        manager.stop()
        manager.stop()  # Should not raise

        assert manager._running is False


class TestTPCalculation:
    """Test TP calculation logic."""

    def _create_manager(self) -> DynamicTPManager:
        """Create a DynamicTPManager for testing."""
        config = DynamicTPConfig(
            enabled=True,
            base_percent=0.3,
            min_percent=0.3,
            max_percent=1.0,
            safety_margin=0.05,
        )
        client = MagicMock()
        order_tracker = MagicMock()
        return DynamicTPManager(config, client, order_tracker, "BTC-USDT")

    def test_calculate_new_tp_zero_funding(self):
        """Test TP calculation with zero funding accumulated."""
        manager = self._create_manager()

        # No funding accumulated: base + margin = 0.3 + 0.05 = 0.35
        new_tp = manager._calculate_new_tp(funding_accumulated=0.0)

        assert new_tp == 0.35

    def test_calculate_new_tp_with_funding(self):
        """Test TP calculation with accumulated funding."""
        manager = self._create_manager()

        # 0.2% funding accumulated: base + funding + margin = 0.3 + 0.2 + 0.05 = 0.55
        new_tp = manager._calculate_new_tp(funding_accumulated=0.2)

        assert new_tp == 0.55

    def test_calculate_new_tp_clamp_min(self):
        """Test that TP is clamped to minimum."""
        manager = self._create_manager()

        # Even with negative funding, TP should be at least min_percent
        new_tp = manager._calculate_new_tp(funding_accumulated=-1.0)

        assert new_tp == 0.3  # min_percent

    def test_calculate_new_tp_clamp_max(self):
        """Test that TP is clamped to maximum."""
        manager = self._create_manager()

        # With very high funding, TP should be capped at max_percent
        new_tp = manager._calculate_new_tp(funding_accumulated=5.0)

        assert new_tp == 1.0  # max_percent

    def test_get_recommended_tp_new_position(self):
        """Test recommended TP for a newly opened position."""
        manager = self._create_manager()

        # 0 hours open, 0.01% funding rate
        tp = manager.get_recommended_tp(hours_open=0, funding_rate=0.0001)

        # 0 funding settlements, so just base + margin
        assert tp == 0.35

    def test_get_recommended_tp_8_hours(self):
        """Test recommended TP for a position open for 8 hours (1 settlement)."""
        manager = self._create_manager()

        # 8 hours = 1 funding settlement
        # Funding = 1 * 0.0001 * 100 = 0.01%
        tp = manager.get_recommended_tp(hours_open=8, funding_rate=0.0001)

        # base + funding + margin = 0.3 + 0.01 + 0.05 = 0.36
        assert round(tp, 2) == 0.36

    def test_get_recommended_tp_24_hours(self):
        """Test recommended TP for a position open for 24 hours (3 settlements)."""
        manager = self._create_manager()

        # 24 hours = 3 funding settlements
        # Funding = 3 * 0.0001 * 100 = 0.03%
        tp = manager.get_recommended_tp(hours_open=24, funding_rate=0.0001)

        # base + funding + margin = 0.3 + 0.03 + 0.05 = 0.38
        assert round(tp, 2) == 0.38

    def test_get_recommended_tp_high_funding(self):
        """Test recommended TP with high funding rate."""
        manager = self._create_manager()

        # 24 hours with high funding rate (0.05% per settlement)
        # Funding = 3 * 0.0005 * 100 = 0.15%
        tp = manager.get_recommended_tp(hours_open=24, funding_rate=0.0005)

        # base + funding + margin = 0.3 + 0.15 + 0.05 = 0.5
        assert round(tp, 2) == 0.50


class TestPositionChecking:
    """Test position checking logic."""

    def _create_manager_with_mocks(self) -> tuple[DynamicTPManager, MagicMock, MagicMock]:
        """Create a DynamicTPManager with accessible mocks."""
        config = DynamicTPConfig(
            enabled=True,
            base_percent=0.3,
            min_percent=0.3,
            max_percent=1.0,
            safety_margin=0.05,
            check_interval_minutes=60,
        )
        client = MagicMock()
        order_tracker = MagicMock()
        manager = DynamicTPManager(config, client, order_tracker, "BTC-USDT")
        return manager, client, order_tracker

    def _create_tracked_order(
        self,
        order_id: str = "order123",
        entry_price: float = 95000.0,
        tp_price: float = 95950.0,  # 1% TP
        hours_ago: float = 10,
    ) -> TrackedOrder:
        """Create a TrackedOrder for testing."""
        order = TrackedOrder(
            order_id=order_id,
            entry_price=entry_price,
            tp_price=tp_price,
            quantity=0.01,
            status=OrderStatus.FILLED,
        )
        order.filled_at = datetime.now() - timedelta(hours=hours_ago)
        return order

    def test_check_positions_no_filled_orders(self):
        """Test that no action is taken when there are no filled orders."""
        manager, client, order_tracker = self._create_manager_with_mocks()
        order_tracker.filled_orders = []

        manager._check_and_update_positions()

        # Should not call get_funding_rate if no orders
        client.get_funding_rate.assert_not_called()

    def test_check_positions_fetches_funding_rate(self):
        """Test that funding rate is fetched when there are filled orders."""
        manager, client, order_tracker = self._create_manager_with_mocks()

        order = self._create_tracked_order()
        order_tracker.filled_orders = [order]
        client.get_funding_rate = MagicMock(
            return_value={"lastFundingRate": 0.0001, "markPrice": 95000}
        )
        client.get_price = MagicMock(return_value=95000.0)

        manager._check_and_update_positions()

        client.get_funding_rate.assert_called_once_with("BTC-USDT")

    def test_check_position_rate_limit(self):
        """Test that positions aren't updated too frequently."""
        manager, client, order_tracker = self._create_manager_with_mocks()

        order = self._create_tracked_order()

        # Mark as recently updated
        manager._last_update[order.order_id] = datetime.now()

        manager._check_position(order, funding_rate=0.0001)

        # Should not update (rate limited)
        assert len(manager._update_history) == 0

    def test_check_position_no_filled_at(self):
        """Test that positions without filled_at are skipped."""
        manager, client, _ = self._create_manager_with_mocks()

        order = TrackedOrder(
            order_id="order123",
            entry_price=95000.0,
            tp_price=95950.0,
            quantity=0.01,
            status=OrderStatus.FILLED,
        )
        # filled_at is None

        manager._check_position(order, funding_rate=0.0001)

        assert len(manager._update_history) == 0


class TestStats:
    """Test statistics reporting."""

    def _create_manager(self) -> DynamicTPManager:
        """Create a DynamicTPManager for testing."""
        config = DynamicTPConfig(enabled=True)
        client = MagicMock()
        order_tracker = MagicMock()
        return DynamicTPManager(config, client, order_tracker, "BTC-USDT")

    def test_get_stats_initial(self):
        """Test initial stats."""
        manager = self._create_manager()

        stats = manager.get_stats()

        assert stats["enabled"] is True
        assert stats["running"] is False
        assert stats["total_updates"] == 0
        assert stats["recent_updates"] == []

    def test_get_stats_with_history(self):
        """Test stats with update history."""
        manager = self._create_manager()

        # Add some update history
        manager._update_history.append(
            PositionTPUpdate(
                order_id="order123",
                old_tp_percent=0.5,
                new_tp_percent=0.6,
                funding_accumulated=0.05,
                updated_at=datetime.now(),
            )
        )

        stats = manager.get_stats()

        assert stats["total_updates"] == 1
        assert len(stats["recent_updates"]) == 1
        assert stats["recent_updates"][0]["order_id"] == "order123"[:8]
        assert stats["recent_updates"][0]["old_tp"] == "0.50%"
        assert stats["recent_updates"][0]["new_tp"] == "0.60%"

    def test_get_positions_needing_update(self):
        """Test getting positions that need updates."""
        manager = self._create_manager()

        # Add update history
        for i in range(15):
            manager._update_history.append(
                PositionTPUpdate(
                    order_id=f"order{i}",
                    old_tp_percent=0.5,
                    new_tp_percent=0.6,
                    funding_accumulated=0.05,
                    updated_at=datetime.now(),
                )
            )

        # Should return only last 10
        positions = manager.get_positions_needing_update()

        assert len(positions) == 10
        assert positions[-1] == "order14"


class TestFundingSettlementCalculation:
    """Test funding settlement frequency constant."""

    def test_funding_settlement_hours(self):
        """Test that funding settlement frequency is 8 hours."""
        config = DynamicTPConfig(enabled=True)
        manager = DynamicTPManager(config, MagicMock(), MagicMock(), "BTC-USDT")

        assert manager.FUNDING_SETTLEMENT_HOURS == 8

    def test_funding_accumulation_formula(self):
        """Test funding accumulation calculation."""
        config = DynamicTPConfig(enabled=True)
        manager = DynamicTPManager(config, MagicMock(), MagicMock(), "BTC-USDT")

        # 24 hours = 3 settlements
        hours_open = 24
        funding_rate = 0.0001  # 0.01%

        funding_settlements = hours_open / manager.FUNDING_SETTLEMENT_HOURS
        funding_accumulated = funding_settlements * abs(funding_rate) * 100

        assert funding_settlements == 3.0
        assert round(funding_accumulated, 4) == 0.03  # 0.03%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
