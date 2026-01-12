"""
Unit tests for EMAFilter class.

Tests the EMA direction filter functionality including EMA calculation,
direction detection, and trade filtering logic.
"""

from src.filters.base import FilterState
from src.filters.ema_filter import EMADirection, EMAFilter


class TestEMAFilterInitialization:
    """Test EMAFilter initialization."""

    def test_default_initialization(self):
        """Test EMAFilter with default parameters."""
        ema_filter = EMAFilter()

        assert ema_filter.name == "ema"
        assert ema_filter.description == "EMA Direction Filter (Impulse System)"
        assert ema_filter.enabled is True
        assert ema_filter.period == 13
        assert ema_filter.timeframe == "1h"
        assert ema_filter.allow_on_rising is True
        assert ema_filter.allow_on_falling is False
        assert ema_filter.direction == EMADirection.FLAT
        assert ema_filter.current_ema is None

    def test_custom_initialization(self):
        """Test EMAFilter with custom parameters."""
        ema_filter = EMAFilter(
            period=21,
            timeframe="4h",
            allow_on_rising=False,
            allow_on_falling=True,
            enabled=False,
        )

        assert ema_filter.period == 21
        assert ema_filter.timeframe == "4h"
        assert ema_filter.allow_on_rising is False
        assert ema_filter.allow_on_falling is True
        assert ema_filter.enabled is False

    def test_initialization_with_enabled_true(self):
        """Test EMAFilter initialized with enabled=True."""
        ema_filter = EMAFilter(enabled=True)
        assert ema_filter.enabled is True

    def test_initialization_with_enabled_false(self):
        """Test EMAFilter initialized with enabled=False."""
        ema_filter = EMAFilter(enabled=False)
        assert ema_filter.enabled is False


class TestEMACalculation:
    """Test EMA calculation logic."""

    def test_ema_calculation_exact_period(self):
        """Test EMA calculation with exactly enough data."""
        ema_filter = EMAFilter(period=3)

        # Create klines with close prices at index 4
        klines = [
            [0, 0, 0, 0, 10.0, 0],
            [0, 0, 0, 0, 11.0, 0],
            [0, 0, 0, 0, 12.0, 0],
            [0, 0, 0, 0, 13.0, 0],
        ]

        ema_filter.update(klines)

        assert ema_filter.current_ema is not None

    def test_ema_calculation_insufficient_data(self):
        """Test EMA calculation with insufficient data returns None."""
        ema_filter = EMAFilter(period=13)

        # Only 5 candles, need at least 14 for period 13
        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 101.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 103.0, 0],
            [0, 0, 0, 0, 104.0, 0],
        ]

        ema_filter.update(klines)

        # Should not calculate EMA with insufficient data
        assert ema_filter.current_ema is None

    def test_ema_update_with_empty_klines(self):
        """Test update with empty klines does nothing."""
        ema_filter = EMAFilter(period=3)
        ema_filter.update([])

        assert ema_filter.current_ema is None
        assert ema_filter.direction == EMADirection.FLAT

    def test_ema_update_with_none_klines(self):
        """Test update with None klines does nothing."""
        ema_filter = EMAFilter(period=3)
        ema_filter.update(None)

        assert ema_filter.current_ema is None


class TestEMADirection:
    """Test EMA direction detection."""

    def test_direction_rising(self):
        """Test rising EMA direction detection."""
        ema_filter = EMAFilter(period=3)

        # Create rising prices
        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 108.0, 0],
        ]

        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.RISING

    def test_direction_falling(self):
        """Test falling EMA direction detection."""
        ema_filter = EMAFilter(period=3)

        # Create falling prices
        klines = [
            [0, 0, 0, 0, 108.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 100.0, 0],
        ]

        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.FALLING

    def test_direction_flat_with_no_data(self):
        """Test flat direction when no data."""
        ema_filter = EMAFilter()
        assert ema_filter.direction == EMADirection.FLAT


class TestShouldAllowTrade:
    """Test should_allow_trade logic."""

    def test_disabled_filter_always_allows(self):
        """Test disabled filter always allows trades."""
        ema_filter = EMAFilter(enabled=False)

        # Even with no data, disabled filter allows
        assert ema_filter.should_allow_trade() is True

    def test_enabled_no_ema_allows(self):
        """Test enabled filter with no EMA calculated allows trades (fail-open)."""
        ema_filter = EMAFilter(enabled=True)

        # No EMA calculated yet
        assert ema_filter.current_ema is None
        assert ema_filter.should_allow_trade() is True

    def test_rising_ema_allows_when_allow_on_rising(self):
        """Test rising EMA allows trade when allow_on_rising=True."""
        ema_filter = EMAFilter(period=3, allow_on_rising=True, allow_on_falling=False)

        # Create rising prices
        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 108.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.RISING
        assert ema_filter.should_allow_trade() is True

    def test_rising_ema_blocks_when_not_allow_on_rising(self):
        """Test rising EMA blocks trade when allow_on_rising=False."""
        ema_filter = EMAFilter(period=3, allow_on_rising=False, allow_on_falling=False)

        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 108.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.RISING
        assert ema_filter.should_allow_trade() is False

    def test_falling_ema_allows_when_allow_on_falling(self):
        """Test falling EMA allows trade when allow_on_falling=True."""
        ema_filter = EMAFilter(period=3, allow_on_rising=False, allow_on_falling=True)

        klines = [
            [0, 0, 0, 0, 108.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 100.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.FALLING
        assert ema_filter.should_allow_trade() is True

    def test_falling_ema_blocks_when_not_allow_on_falling(self):
        """Test falling EMA blocks trade when allow_on_falling=False."""
        ema_filter = EMAFilter(period=3, allow_on_rising=True, allow_on_falling=False)

        klines = [
            [0, 0, 0, 0, 108.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 100.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.FALLING
        assert ema_filter.should_allow_trade() is False


class TestShouldProtectOrders:
    """Test should_protect_orders logic."""

    def test_disabled_filter_does_not_protect(self):
        """Test disabled filter does not protect orders."""
        ema_filter = EMAFilter(enabled=False)
        assert ema_filter.should_protect_orders() is False

    def test_rising_ema_protects_orders(self):
        """Test rising EMA protects orders."""
        ema_filter = EMAFilter(period=3)

        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 108.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.RISING
        assert ema_filter.should_protect_orders() is True

    def test_falling_ema_does_not_protect(self):
        """Test falling EMA does not protect orders."""
        ema_filter = EMAFilter(period=3)

        klines = [
            [0, 0, 0, 0, 108.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 100.0, 0],
        ]
        ema_filter.update(klines)

        assert ema_filter.direction == EMADirection.FALLING
        assert ema_filter.should_protect_orders() is False


class TestGetState:
    """Test get_state method."""

    def test_get_state_returns_filter_state(self):
        """Test get_state returns FilterState object."""
        ema_filter = EMAFilter(period=13, timeframe="4h")

        state = ema_filter.get_state()

        assert isinstance(state, FilterState)
        assert state.enabled is True
        assert state.description == "EMA Direction Filter (Impulse System)"
        assert state.details["period"] == 13
        assert state.details["timeframe"] == "4h"
        assert state.details["direction"] == "flat"
        assert state.details["allow_on_rising"] is True
        assert state.details["allow_on_falling"] is False

    def test_get_state_with_ema_values(self):
        """Test get_state includes EMA values after update."""
        ema_filter = EMAFilter(period=3)

        klines = [
            [0, 0, 0, 0, 100.0, 0],
            [0, 0, 0, 0, 102.0, 0],
            [0, 0, 0, 0, 104.0, 0],
            [0, 0, 0, 0, 106.0, 0],
            [0, 0, 0, 0, 108.0, 0],
        ]
        ema_filter.update(klines)

        state = ema_filter.get_state()

        assert state.details["current_ema"] is not None
        assert state.details["previous_ema"] is not None
        assert state.details["last_close"] == 108.0
        assert state.details["direction"] == "rising"


class TestSyncConfig:
    """Test sync_config method."""

    def test_sync_config_updates_all_fields(self):
        """Test sync_config updates all configuration fields."""
        ema_filter = EMAFilter()

        ema_filter.sync_config(
            enabled=False,
            period=21,
            timeframe="4h",
            allow_on_rising=False,
            allow_on_falling=True,
        )

        assert ema_filter.enabled is False
        assert ema_filter.period == 21
        assert ema_filter.timeframe == "4h"
        assert ema_filter.allow_on_rising is False
        assert ema_filter.allow_on_falling is True


class TestEnableDisable:
    """Test enable/disable functionality."""

    def test_enable(self):
        """Test enabling filter."""
        ema_filter = EMAFilter(enabled=False)
        assert ema_filter.enabled is False

        ema_filter.enable()
        assert ema_filter.enabled is True

    def test_disable(self):
        """Test disabling filter."""
        ema_filter = EMAFilter(enabled=True)
        assert ema_filter.enabled is True

        ema_filter.disable()
        assert ema_filter.enabled is False

    def test_set_enabled(self):
        """Test set_enabled method."""
        ema_filter = EMAFilter()

        ema_filter.set_enabled(False)
        assert ema_filter.enabled is False

        ema_filter.set_enabled(True)
        assert ema_filter.enabled is True


class TestPropertySetters:
    """Test property setters."""

    def test_period_setter(self):
        """Test period setter."""
        ema_filter = EMAFilter()
        ema_filter.period = 21
        assert ema_filter.period == 21

    def test_timeframe_setter(self):
        """Test timeframe setter."""
        ema_filter = EMAFilter()
        ema_filter.timeframe = "4h"
        assert ema_filter.timeframe == "4h"

    def test_allow_on_rising_setter(self):
        """Test allow_on_rising setter."""
        ema_filter = EMAFilter()
        ema_filter.allow_on_rising = False
        assert ema_filter.allow_on_rising is False

    def test_allow_on_falling_setter(self):
        """Test allow_on_falling setter."""
        ema_filter = EMAFilter()
        ema_filter.allow_on_falling = True
        assert ema_filter.allow_on_falling is True
