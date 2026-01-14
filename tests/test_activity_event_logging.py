"""
Tests for activity event logging in GridManager.

Tests:
1. _log_activity_event method behavior
2. PAUSE state restoration fix
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from config import MACDConfig
from src.database.models.activity_event import EventType
from src.strategy.macd_strategy import GridState, MACDStrategy


class TestLogActivityEventMethod:
    """Tests for _log_activity_event method in GridManager."""

    @pytest.fixture
    def mock_grid_manager(self):
        """Create a mock GridManager with activity event repository."""
        # Create a minimal mock
        gm = MagicMock()
        gm._account_id = uuid4()
        gm._activity_event_repository = MagicMock()
        gm._activity_event_repository.create_event = MagicMock(return_value=MagicMock())
        return gm

    def test_log_activity_event_skips_without_repository(self):
        """Test that logging is skipped when repository is None."""
        # Import here to avoid circular imports
        from src.grid.grid_manager import GridManager

        # Create a partial mock - just test the method logic
        gm = MagicMock(spec=GridManager)
        gm._activity_event_repository = None
        gm._account_id = uuid4()

        # Call the actual method - it should return early
        GridManager._log_activity_event(gm, EventType.BOT_STARTED, "Test", {})
        # No assertion needed - just verify no exception is raised

    def test_log_activity_event_skips_without_account_id(self):
        """Test that logging is skipped when account_id is None."""
        from src.grid.grid_manager import GridManager

        gm = MagicMock(spec=GridManager)
        gm._activity_event_repository = MagicMock()
        gm._account_id = None

        GridManager._log_activity_event(gm, EventType.BOT_STARTED, "Test", {})
        # Verify create_event was never called
        gm._activity_event_repository.create_event.assert_not_called()


class TestPauseStateRestoration:
    """Tests for PAUSE state restoration fix in MACDStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        return MACDStrategy(config)

    def test_restore_state_pause_not_restored(self, strategy):
        """Test that PAUSE state is not restored to prevent stuck state."""
        # Restore with PAUSE state
        strategy.restore_state(cycle_activated=True, last_state="pause")

        # PAUSE should NOT be restored - _prev_state should be None
        assert strategy._prev_state is None
        # cycle_activated should still be restored
        assert strategy._cycle_activated is True
        assert strategy._trigger_activated is True

    def test_restore_state_active_is_restored(self, strategy):
        """Test that ACTIVE state IS restored normally."""
        strategy.restore_state(cycle_activated=True, last_state="active")

        # ACTIVE should be restored
        assert strategy._prev_state == GridState.ACTIVE
        assert strategy._cycle_activated is True

    def test_restore_state_activate_is_restored(self, strategy):
        """Test that ACTIVATE state IS restored normally."""
        strategy.restore_state(cycle_activated=True, last_state="activate")

        # ACTIVATE should be restored
        assert strategy._prev_state == GridState.ACTIVATE
        assert strategy._cycle_activated is True

    def test_restore_state_inactive_is_restored(self, strategy):
        """Test that INACTIVE state IS restored normally."""
        strategy.restore_state(cycle_activated=False, last_state="inactive")

        # INACTIVE should be restored
        assert strategy._prev_state == GridState.INACTIVE
        assert strategy._cycle_activated is False

    def test_restore_state_wait_is_restored(self, strategy):
        """Test that WAIT state IS restored normally."""
        strategy.restore_state(cycle_activated=False, last_state="wait")

        # WAIT should be restored
        assert strategy._prev_state == GridState.WAIT
        assert strategy._cycle_activated is False

    def test_restore_state_invalid_defaults_to_wait(self, strategy):
        """Test that invalid state defaults to WAIT."""
        strategy.restore_state(cycle_activated=False, last_state="invalid_state")

        # Should default to WAIT
        assert strategy._prev_state == GridState.WAIT

    def test_restore_state_pause_uppercase(self, strategy):
        """Test that PAUSE state is handled case-insensitively."""
        strategy.restore_state(cycle_activated=True, last_state="PAUSE")

        # PAUSE should NOT be restored even in uppercase
        assert strategy._prev_state is None
        assert strategy._cycle_activated is True

    def test_restore_state_pause_mixed_case(self, strategy):
        """Test that PAUSE state is handled case-insensitively (mixed case)."""
        strategy.restore_state(cycle_activated=True, last_state="Pause")

        # PAUSE should NOT be restored
        assert strategy._prev_state is None
        assert strategy._cycle_activated is True


class TestEventTypeEnum:
    """Tests for EventType enum values used in logging."""

    def test_all_event_types_exist(self):
        """Verify all expected event types exist."""
        expected_types = [
            "ORDER_FILLED",
            "TRADE_CLOSED",
            "STRATEGY_PAUSED",
            "STRATEGY_RESUMED",
            "TP_ADJUSTED",
            "CYCLE_ACTIVATED",
            "CYCLE_DEACTIVATED",
            "BOT_STARTED",
            "BOT_STOPPED",
            "ERROR_OCCURRED",
        ]
        for event_type in expected_types:
            assert hasattr(EventType, event_type), f"Missing EventType: {event_type}"

    def test_event_type_values(self):
        """Verify event type values match expected strings."""
        assert EventType.BOT_STARTED.value == "BOT_STARTED"
        assert EventType.BOT_STOPPED.value == "BOT_STOPPED"
        assert EventType.CYCLE_ACTIVATED.value == "CYCLE_ACTIVATED"
        assert EventType.STRATEGY_PAUSED.value == "STRATEGY_PAUSED"
        assert EventType.ORDER_FILLED.value == "ORDER_FILLED"
        assert EventType.TRADE_CLOSED.value == "TRADE_CLOSED"
        assert EventType.ERROR_OCCURRED.value == "ERROR_OCCURRED"
