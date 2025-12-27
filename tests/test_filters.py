"""
Unit tests for filter system.

Tests the Filter base class, FilterRegistry, and MACDFilter.
"""

import pytest

from config import MACDConfig
from src.filters.base import Filter, FilterState
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.strategy.macd_strategy import GridState, MACDStrategy

# Test Filter Base Class


class DummyFilter(Filter):
    """Dummy filter for testing base class."""

    def __init__(self, name: str = "test", description: str = "Test Filter"):
        super().__init__(name, description)
        self._allow_trade = True

    def should_allow_trade(self) -> bool:
        return self.enabled and self._allow_trade

    def get_state(self) -> FilterState:
        return FilterState(
            enabled=self.enabled,
            description=self.description,
            details={"allow_trade": self._allow_trade},
        )

    def set_allow_trade(self, allow: bool):
        self._allow_trade = allow


class TestFilterBase:
    """Test Filter base class."""

    def test_filter_initialization(self):
        """Test filter is initialized correctly."""
        filter_obj = DummyFilter("test", "Test Filter")
        assert filter_obj.name == "test"
        assert filter_obj.description == "Test Filter"
        assert filter_obj.enabled is True  # Default enabled

    def test_filter_enable_disable(self):
        """Test enabling and disabling filters."""
        filter_obj = DummyFilter()

        # Start enabled
        assert filter_obj.enabled is True

        # Disable
        filter_obj.disable()
        assert filter_obj.enabled is False

        # Enable
        filter_obj.enable()
        assert filter_obj.enabled is True

    def test_filter_set_enabled(self):
        """Test set_enabled method."""
        filter_obj = DummyFilter()

        filter_obj.set_enabled(False)
        assert filter_obj.enabled is False

        filter_obj.set_enabled(True)
        assert filter_obj.enabled is True

    def test_filter_should_allow_trade(self):
        """Test should_allow_trade respects enabled state."""
        filter_obj = DummyFilter()

        # Enabled and allowed
        assert filter_obj.should_allow_trade() is True

        # Disabled (should block)
        filter_obj.disable()
        assert filter_obj.should_allow_trade() is False

        # Re-enable
        filter_obj.enable()
        assert filter_obj.should_allow_trade() is True

        # Internal logic blocks
        filter_obj.set_allow_trade(False)
        assert filter_obj.should_allow_trade() is False

    def test_filter_get_state(self):
        """Test get_state returns correct info."""
        filter_obj = DummyFilter("myfilter", "My Filter")

        state = filter_obj.get_state()
        assert isinstance(state, FilterState)
        assert state.enabled is True
        assert state.description == "My Filter"
        assert state.details["allow_trade"] is True


# Test FilterRegistry


class TestFilterRegistry:
    """Test FilterRegistry singleton and operations."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        registry = FilterRegistry()
        registry.clear()
        yield
        registry.clear()

    def test_registry_singleton(self):
        """Test registry is a singleton."""
        r1 = FilterRegistry()
        r2 = FilterRegistry()
        assert r1 is r2

    def test_register_filter(self):
        """Test registering a filter."""
        registry = FilterRegistry()
        filter_obj = DummyFilter("test1", "Test 1")

        registry.register(filter_obj)
        assert registry.get_filter("test1") is filter_obj
        assert "test1" in registry.list_filters()

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate filter raises error."""
        registry = FilterRegistry()
        filter_obj1 = DummyFilter("test1", "Test 1")
        filter_obj2 = DummyFilter("test1", "Test 1 Duplicate")

        registry.register(filter_obj1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(filter_obj2)

    def test_get_filter(self):
        """Test getting filter by name."""
        registry = FilterRegistry()
        filter_obj = DummyFilter("test1", "Test 1")
        registry.register(filter_obj)

        assert registry.get_filter("test1") is filter_obj
        assert registry.get_filter("nonexistent") is None

    def test_enable_disable_filter(self):
        """Test enabling and disabling filters."""
        registry = FilterRegistry()
        filter_obj = DummyFilter("test1", "Test 1")
        registry.register(filter_obj)

        # Disable
        success = registry.disable_filter("test1")
        assert success is True
        assert filter_obj.enabled is False

        # Enable
        success = registry.enable_filter("test1")
        assert success is True
        assert filter_obj.enabled is True

        # Try to disable nonexistent
        success = registry.disable_filter("nonexistent")
        assert success is False

    def test_enable_all_disable_all(self):
        """Test bulk enable/disable operations."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")
        f3 = DummyFilter("f3", "Filter 3")

        registry.register(f1)
        registry.register(f2)
        registry.register(f3)

        # Disable all
        registry.disable_all()
        assert f1.enabled is False
        assert f2.enabled is False
        assert f3.enabled is False

        # Enable all
        registry.enable_all()
        assert f1.enabled is True
        assert f2.enabled is True
        assert f3.enabled is True

    def test_should_allow_trade_no_filters(self):
        """Test should_allow_trade returns True when no filters registered."""
        registry = FilterRegistry()
        assert registry.should_allow_trade() is True

    def test_should_allow_trade_all_disabled(self):
        """Test should_allow_trade returns True when all filters disabled."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        registry.register(f1)
        registry.register(f2)
        registry.disable_all()

        # All disabled = allow trade
        assert registry.should_allow_trade() is True

    def test_should_allow_trade_all_enabled_allow(self):
        """Test should_allow_trade when all enabled filters allow."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        f1.set_allow_trade(True)
        f2.set_allow_trade(True)

        registry.register(f1)
        registry.register(f2)

        # All allow
        assert registry.should_allow_trade() is True

    def test_should_allow_trade_one_blocks(self):
        """Test should_allow_trade when one filter blocks."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        f1.set_allow_trade(True)
        f2.set_allow_trade(False)  # Blocks

        registry.register(f1)
        registry.register(f2)

        # One blocks = block trade
        assert registry.should_allow_trade() is False

    def test_should_allow_trade_mixed_enabled(self):
        """Test should_allow_trade with mix of enabled/disabled."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        f1.set_allow_trade(True)
        f2.set_allow_trade(False)  # Would block but disabled

        registry.register(f1)
        registry.register(f2)

        # Disable f2
        f2.disable()

        # Only f1 enabled and allows = allow trade
        assert registry.should_allow_trade() is True

    def test_get_all_states(self):
        """Test get_all_states returns correct info."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        registry.register(f1)
        registry.register(f2)

        states = registry.get_all_states()

        assert states["total_count"] == 2
        assert states["enabled_count"] == 2
        assert states["all_enabled"] is True
        assert states["any_enabled"] is True

        # Disable one
        f1.disable()
        states = registry.get_all_states()

        assert states["enabled_count"] == 1
        assert states["all_enabled"] is False
        assert states["any_enabled"] is True

        # Disable all
        f2.disable()
        states = registry.get_all_states()

        assert states["enabled_count"] == 0
        assert states["all_enabled"] is False
        assert states["any_enabled"] is False

    def test_list_filters(self):
        """Test list_filters returns all filter names."""
        registry = FilterRegistry()
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        registry.register(f1)
        registry.register(f2)

        names = registry.list_filters()
        assert "f1" in names
        assert "f2" in names
        assert len(names) == 2


# Test MACDFilter


class TestMACDFilter:
    """Test MACDFilter integration with MACDStrategy."""

    @pytest.fixture
    def macd_strategy(self):
        """Create a mock MACDStrategy."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        return MACDStrategy(config)

    @pytest.fixture
    def macd_filter(self, macd_strategy):
        """Create MACDFilter instance."""
        return MACDFilter(macd_strategy)

    def test_macd_filter_initialization(self, macd_filter, macd_strategy):
        """Test MACDFilter is initialized correctly."""
        assert macd_filter.name == "macd"
        assert macd_filter.description == "MACD Crossover Strategy"
        assert macd_filter.enabled is True
        assert macd_filter._strategy is macd_strategy

    def test_macd_filter_disabled_always_allows(self, macd_filter):
        """Test disabled MACDFilter always allows trades."""
        macd_filter.disable()
        macd_filter.set_current_state(GridState.WAIT)

        # Even in WAIT state, disabled filter allows
        assert macd_filter.should_allow_trade() is True

        macd_filter.set_current_state(GridState.INACTIVE)
        assert macd_filter.should_allow_trade() is True

    def test_macd_filter_enabled_respects_state(self, macd_filter, macd_strategy):
        """Test enabled MACDFilter respects MACD state."""
        # Manually activate cycle (required for orders)
        macd_strategy.manual_activate()

        # ACTIVATE state - should allow
        macd_filter.set_current_state(GridState.ACTIVATE)
        assert macd_filter.should_allow_trade() is True

        # ACTIVE state - should allow
        macd_filter.set_current_state(GridState.ACTIVE)
        assert macd_filter.should_allow_trade() is True

        # PAUSE state - should not allow
        macd_filter.set_current_state(GridState.PAUSE)
        assert macd_filter.should_allow_trade() is False

        # WAIT state - should not allow
        macd_filter.set_current_state(GridState.WAIT)
        assert macd_filter.should_allow_trade() is False

        # INACTIVE state - should not allow
        macd_filter.set_current_state(GridState.INACTIVE)
        assert macd_filter.should_allow_trade() is False

    def test_macd_filter_get_state(self, macd_filter, macd_strategy):
        """Test get_state returns MACD details."""
        macd_filter.set_current_state(GridState.ACTIVATE)
        macd_strategy.manual_activate()

        state = macd_filter.get_state()

        assert state.enabled is True
        assert state.description == "MACD Crossover Strategy"
        assert state.details["current_state"] == "activate"
        assert state.details["cycle_activated"] is True
        assert "state_description" in state.details

    def test_macd_filter_manual_activate_deactivate(self, macd_filter, macd_strategy):
        """Test manual activate/deactivate."""
        # Initially not activated
        assert macd_strategy.is_cycle_activated is False

        # Activate
        success = macd_filter.manual_activate()
        assert success is True
        assert macd_strategy.is_cycle_activated is True

        # Deactivate
        macd_filter.manual_deactivate()
        assert macd_strategy.is_cycle_activated is False


# Integration test with registry


class TestFilterRegistryIntegration:
    """Test FilterRegistry with MACDFilter."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        registry = FilterRegistry()
        registry.clear()
        yield
        registry.clear()

    def test_registry_with_macd_filter(self):
        """Test registering and using MACDFilter in registry."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)
        macd_filter = MACDFilter(strategy)

        registry = FilterRegistry()
        registry.register(macd_filter)

        # Initially enabled, cycle not activated - should not allow
        assert registry.should_allow_trade() is False

        # Manually activate cycle
        strategy.manual_activate()
        macd_filter.set_current_state(GridState.ACTIVATE)

        # Now should allow
        assert registry.should_allow_trade() is True

        # Disable filter - should allow (no filters active)
        registry.disable_filter("macd")
        assert registry.should_allow_trade() is True

        # Re-enable
        registry.enable_filter("macd")
        assert registry.should_allow_trade() is True

    def test_multiple_filters_combined(self):
        """Test multiple filters working together."""
        registry = FilterRegistry()

        # Add dummy filters
        f1 = DummyFilter("f1", "Filter 1")
        f2 = DummyFilter("f2", "Filter 2")

        f1.set_allow_trade(True)
        f2.set_allow_trade(True)

        registry.register(f1)
        registry.register(f2)

        # Both allow
        assert registry.should_allow_trade() is True

        # One blocks
        f1.set_allow_trade(False)
        assert registry.should_allow_trade() is False

        # Disable the blocking one
        f1.disable()
        assert registry.should_allow_trade() is True  # Only f2 enabled, allows

        # Disable all
        registry.disable_all()
        assert registry.should_allow_trade() is True  # No filters = allow
