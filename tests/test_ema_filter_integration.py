"""
Integration tests for EMA filter integration with GridManager.

Tests the integration of EMAFilter with:
- FilterRegistry registration and sync
- GridManager main loop updates
- Order protection logic
- WebSocket broadcast with EMA state
"""

import pytest

from config import MACDConfig
from src.filters.ema_filter import EMADirection, EMAFilter
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.strategy.macd_strategy import GridState, MACDStrategy


class TestEMAFilterRegistration:
    """Test EMA filter registration with FilterRegistry."""

    def test_ema_filter_registered_in_registry(self):
        """Test that EMA filter can be registered in FilterRegistry."""
        registry = FilterRegistry()
        registry.clear()  # Clear singleton state

        ema_filter = EMAFilter()
        registry.register(ema_filter)

        assert registry.get_filter("ema") is ema_filter
        assert "ema" in registry.list_filters()

    def test_dual_filter_registration(self):
        """Test both MACD and EMA filters can be registered."""
        registry = FilterRegistry()
        registry.clear()

        macd_config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(macd_config)
        macd_filter = MACDFilter(strategy)
        ema_filter = EMAFilter()

        registry.register(macd_filter)
        registry.register(ema_filter)

        assert len(registry.list_filters()) == 2
        assert "macd" in registry.list_filters()
        assert "ema" in registry.list_filters()

    def test_duplicate_registration_raises_error(self):
        """Test that registering same filter twice raises error."""
        registry = FilterRegistry()
        registry.clear()

        ema_filter1 = EMAFilter()
        ema_filter2 = EMAFilter()

        registry.register(ema_filter1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(ema_filter2)


class TestSyncEMAFilter:
    """Test FilterRegistry sync_ema_filter method."""

    def test_sync_ema_filter_updates_config(self):
        """Test sync_ema_filter updates filter configuration."""
        registry = FilterRegistry()
        registry.clear()

        ema_filter = EMAFilter()
        registry.register(ema_filter)

        result = registry.sync_ema_filter(
            enabled=False,
            period=21,
            timeframe="4h",
            allow_on_rising=False,
            allow_on_falling=True,
        )

        assert result is True
        assert ema_filter.enabled is False
        assert ema_filter.period == 21
        assert ema_filter.timeframe == "4h"
        assert ema_filter.allow_on_rising is False
        assert ema_filter.allow_on_falling is True

    def test_sync_ema_filter_no_filter_returns_false(self):
        """Test sync_ema_filter returns False when no EMA filter registered."""
        registry = FilterRegistry()
        registry.clear()

        result = registry.sync_ema_filter(
            enabled=True,
            period=13,
            timeframe="1h",
            allow_on_rising=True,
            allow_on_falling=False,
        )

        assert result is False


class TestFilterRegistryShouldAllowTrade:
    """Test combined filter logic in FilterRegistry."""

    def test_both_filters_enabled_both_allow(self):
        """Test trade allowed when both filters allow."""
        registry = FilterRegistry()
        registry.clear()

        macd_config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(macd_config)
        macd_filter = MACDFilter(strategy, enabled=True)
        ema_filter = EMAFilter(enabled=True)

        registry.register(macd_filter)
        registry.register(ema_filter)

        # Activate MACD cycle and trigger (required by strategy)
        strategy.manual_activate()
        strategy.set_trigger(True)

        # Set MACD to allow trades
        macd_filter.set_current_state(GridState.ACTIVE)

        # Set EMA to rising (allow)
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        assert registry.should_allow_trade() is True

    def test_macd_allows_ema_blocks(self):
        """Test trade blocked when EMA filter blocks."""
        registry = FilterRegistry()
        registry.clear()

        macd_config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(macd_config)
        macd_filter = MACDFilter(strategy, enabled=True)
        ema_filter = EMAFilter(enabled=True, allow_on_rising=True, allow_on_falling=False)

        registry.register(macd_filter)
        registry.register(ema_filter)

        # Activate MACD cycle and trigger (required by strategy)
        strategy.manual_activate()
        strategy.set_trigger(True)

        # Set MACD to allow trades
        macd_filter.set_current_state(GridState.ACTIVE)

        # Set EMA to falling (block)
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        assert ema_filter.direction == EMADirection.FALLING
        assert registry.should_allow_trade() is False

    def test_ema_disabled_allows_trade(self):
        """Test trade allowed when EMA filter is disabled."""
        registry = FilterRegistry()
        registry.clear()

        macd_config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(macd_config)
        macd_filter = MACDFilter(strategy, enabled=True)
        ema_filter = EMAFilter(enabled=False)  # Disabled

        registry.register(macd_filter)
        registry.register(ema_filter)

        # Activate MACD cycle and trigger (required by strategy)
        strategy.manual_activate()
        strategy.set_trigger(True)

        # Set MACD to allow trades
        macd_filter.set_current_state(GridState.ACTIVE)

        # Even with falling EMA, disabled filter allows
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        assert registry.should_allow_trade() is True


class TestOrderProtectionLogic:
    """Test EMA protection logic for orders."""

    def test_protection_when_ema_rising(self):
        """Test orders are protected when EMA is rising."""
        ema_filter = EMAFilter(enabled=True)

        # Set EMA to rising
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        assert ema_filter.direction == EMADirection.RISING
        assert ema_filter.should_protect_orders() is True

    def test_no_protection_when_ema_falling(self):
        """Test orders are not protected when EMA is falling."""
        ema_filter = EMAFilter(enabled=True)

        # Set EMA to falling
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        assert ema_filter.direction == EMADirection.FALLING
        assert ema_filter.should_protect_orders() is False

    def test_no_protection_when_disabled(self):
        """Test orders are not protected when filter is disabled."""
        ema_filter = EMAFilter(enabled=False)

        # Even with rising EMA
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        assert ema_filter.should_protect_orders() is False


class TestEMADirectionChangeTracking:
    """Test EMA direction change detection."""

    def test_direction_change_rising_to_falling(self):
        """Test detection of direction change from rising to falling."""
        ema_filter = EMAFilter(period=3)

        # First, set to rising
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(10)]
        ema_filter.update(rising_klines)
        assert ema_filter.direction == EMADirection.RISING

        # Then, set to falling
        falling_klines = [[0, 0, 0, 0, float(120 - i * 3), 0] for i in range(10)]
        ema_filter.update(falling_klines)
        assert ema_filter.direction == EMADirection.FALLING

    def test_direction_change_falling_to_rising(self):
        """Test detection of direction change from falling to rising."""
        ema_filter = EMAFilter(period=3)

        # First, set to falling
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(10)]
        ema_filter.update(falling_klines)
        assert ema_filter.direction == EMADirection.FALLING

        # Then, set to rising
        rising_klines = [[0, 0, 0, 0, float(90 + i * 3), 0] for i in range(10)]
        ema_filter.update(rising_klines)
        assert ema_filter.direction == EMADirection.RISING


class TestEMAFilterState:
    """Test EMA filter state for WebSocket broadcasts."""

    def test_get_state_includes_all_fields(self):
        """Test get_state includes all required fields for broadcast."""
        ema_filter = EMAFilter(period=13, timeframe="1h")

        # Update with some data
        klines = [[0, 0, 0, 0, float(100 + i), 0] for i in range(20)]
        ema_filter.update(klines)

        state = ema_filter.get_state()

        assert state.enabled is True
        assert "period" in state.details
        assert "timeframe" in state.details
        assert "current_ema" in state.details
        assert "direction" in state.details
        assert "allow_on_rising" in state.details
        assert "allow_on_falling" in state.details

    def test_state_matches_filter_config(self):
        """Test state values match filter configuration."""
        ema_filter = EMAFilter(
            period=21,
            timeframe="4h",
            allow_on_rising=False,
            allow_on_falling=True,
            enabled=False,
        )

        state = ema_filter.get_state()

        assert state.enabled is False
        assert state.details["period"] == 21
        assert state.details["timeframe"] == "4h"
        assert state.details["allow_on_rising"] is False
        assert state.details["allow_on_falling"] is True


class TestDecisionMatrix:
    """Test the complete decision matrix for trade/cancel actions."""

    @pytest.fixture
    def setup_filters(self):
        """Set up MACD and EMA filters with registry."""
        registry = FilterRegistry()
        registry.clear()

        macd_config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(macd_config)
        macd_filter = MACDFilter(strategy, enabled=True)
        ema_filter = EMAFilter(enabled=True)

        # Activate MACD cycle and trigger (required by strategy)
        strategy.manual_activate()
        strategy.set_trigger(True)

        registry.register(macd_filter)
        registry.register(ema_filter)

        return registry, macd_filter, ema_filter

    def test_active_state_rising_ema_creates_orders(self, setup_filters):
        """Test: ACTIVE + RISING EMA = Create orders."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.ACTIVE)
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        assert registry.should_allow_trade() is True
        assert ema_filter.should_protect_orders() is True

    def test_active_state_falling_ema_blocks_orders(self, setup_filters):
        """Test: ACTIVE + FALLING EMA = Block order creation."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.ACTIVE)
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        assert registry.should_allow_trade() is False
        assert ema_filter.should_protect_orders() is False

    def test_inactive_state_rising_ema_protects_orders(self, setup_filters):
        """Test: INACTIVE + RISING EMA = Protect orders (no cancel)."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.INACTIVE)
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        # Should NOT allow trade (INACTIVE)
        assert registry.should_allow_trade() is False
        # But should protect orders (EMA rising)
        assert ema_filter.should_protect_orders() is True

    def test_inactive_state_falling_ema_allows_cancel(self, setup_filters):
        """Test: INACTIVE + FALLING EMA = Cancel orders."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.INACTIVE)
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        # Should NOT allow trade (INACTIVE)
        assert registry.should_allow_trade() is False
        # Should NOT protect orders (EMA falling)
        assert ema_filter.should_protect_orders() is False

    def test_pause_state_no_action(self, setup_filters):
        """Test: PAUSE state = No create, no cancel."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.PAUSE)
        # EMA direction doesn't matter for PAUSE state
        rising_klines = [[0, 0, 0, 0, float(100 + i * 2), 0] for i in range(20)]
        ema_filter.update(rising_klines)

        # MACD filter blocks in PAUSE state
        assert macd_filter.should_allow_trade() is False
        assert registry.should_allow_trade() is False

    def test_ema_disabled_ignores_direction(self, setup_filters):
        """Test: EMA disabled = Ignore EMA direction."""
        registry, macd_filter, ema_filter = setup_filters

        macd_filter.set_current_state(GridState.ACTIVE)
        ema_filter.disable()

        # Even with falling EMA, disabled filter allows
        falling_klines = [[0, 0, 0, 0, float(120 - i * 2), 0] for i in range(20)]
        ema_filter.update(falling_klines)

        assert registry.should_allow_trade() is True
        assert ema_filter.should_protect_orders() is False


class TestWebSocketEventModels:
    """Test WebSocket event models include EMA status."""

    def test_ema_status_data_model(self):
        """Test EMAStatusData model structure."""
        from src.api.websocket.events import EMAStatusData

        ema_status = EMAStatusData(
            enabled=True,
            period=13,
            timeframe="1h",
            value=95000.0,
            direction="rising",
            allow_trade=True,
        )

        assert ema_status.enabled is True
        assert ema_status.period == 13
        assert ema_status.timeframe == "1h"
        assert ema_status.value == 95000.0
        assert ema_status.direction == "rising"
        assert ema_status.allow_trade is True

    def test_filters_status_data_model(self):
        """Test FiltersStatusData model structure."""
        from src.api.websocket.events import FiltersStatusData

        filters_status = FiltersStatusData(should_allow_trade=True)

        assert filters_status.should_allow_trade is True

    def test_bot_status_event_includes_ema(self):
        """Test BotStatusEvent includes EMA and filters status."""
        from src.api.websocket.events import BotStatusEvent, EMAStatusData, FiltersStatusData

        ema_status = EMAStatusData(
            enabled=True,
            period=13,
            timeframe="1h",
            value=95000.0,
            direction="rising",
            allow_trade=True,
        )

        filters_status = FiltersStatusData(should_allow_trade=True)

        bot_status = BotStatusEvent(
            state="ACTIVE",
            is_running=True,
            macd_line=0.5,
            histogram=0.1,
            ema=ema_status,
            filters=filters_status,
        )

        assert bot_status.ema is not None
        assert bot_status.ema.enabled is True
        assert bot_status.ema.direction == "rising"
        assert bot_status.filters is not None
        assert bot_status.filters.should_allow_trade is True
