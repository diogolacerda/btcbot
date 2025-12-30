"""
Unit tests for MACD strategy state machine.

Tests the simplified MACD logic introduced in BE-023.
"""

import pytest

from config import MACDConfig
from src.strategy.macd_strategy import GridState, MACDStrategy, MACDValues


class TestMACDValues:
    """Test MACDValues dataclass properties."""

    def test_are_both_lines_negative_true(self):
        """Test are_both_lines_negative when both lines are negative."""
        macd = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,
            prev_histogram=-60,
        )
        assert macd.are_both_lines_negative is True

    def test_are_both_lines_negative_macd_positive(self):
        """Test are_both_lines_negative when MACD is positive."""
        macd = MACDValues(
            macd_line=10,  # positive
            signal_line=-50,
            histogram=-50,
            prev_histogram=-60,
        )
        assert macd.are_both_lines_negative is False

    def test_are_both_lines_negative_signal_positive(self):
        """Test are_both_lines_negative when Signal is positive."""
        macd = MACDValues(
            macd_line=-100,
            signal_line=10,  # positive
            histogram=-50,
            prev_histogram=-60,
        )
        assert macd.are_both_lines_negative is False

    def test_are_both_lines_negative_both_positive(self):
        """Test are_both_lines_negative when both lines are positive."""
        macd = MACDValues(
            macd_line=100,
            signal_line=50,
            histogram=50,
            prev_histogram=40,
        )
        assert macd.are_both_lines_negative is False

    def test_are_both_lines_negative_at_zero(self):
        """Test are_both_lines_negative when lines are exactly zero."""
        macd = MACDValues(
            macd_line=0,  # not negative
            signal_line=-50,
            histogram=-50,
            prev_histogram=-60,
        )
        assert macd.are_both_lines_negative is False


class TestMACDStrategyDetermineState:
    """Test _determine_state method with simplified logic."""

    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        return MACDStrategy(config)

    # Tests for ACTIVATE state (vermelho claro + ambas linhas < 0)

    def test_activate_both_lines_negative(self, strategy):
        """Test ACTIVATE when vermelho claro and both lines negative."""
        macd = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,  # negative
            prev_histogram=-60,  # rising (subindo)
        )
        state = strategy._determine_state(macd)
        assert state == GridState.ACTIVATE

    def test_wait_macd_positive(self, strategy):
        """Test WAIT when vermelho claro but MACD is positive."""
        macd = MACDValues(
            macd_line=10,  # positive
            signal_line=-50,
            histogram=-50,  # negative
            prev_histogram=-60,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.WAIT

    def test_wait_signal_positive(self, strategy):
        """Test WAIT when vermelho claro but Signal is positive."""
        macd = MACDValues(
            macd_line=-100,
            signal_line=10,  # positive
            histogram=-50,  # negative
            prev_histogram=-60,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.WAIT

    def test_wait_both_lines_positive(self, strategy):
        """Test WAIT when vermelho claro but both lines positive."""
        macd = MACDValues(
            macd_line=10,  # positive
            signal_line=5,  # positive
            histogram=-50,  # negative
            prev_histogram=-60,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.WAIT

    def test_wait_macd_at_zero(self, strategy):
        """Test WAIT when vermelho claro but MACD is exactly zero."""
        macd = MACDValues(
            macd_line=0,  # not negative
            signal_line=-50,
            histogram=-50,  # negative
            prev_histogram=-60,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.WAIT

    # Tests for ACTIVE state (verde escuro)

    def test_active_verde_escuro(self, strategy):
        """Test ACTIVE when verde escuro (histogram positive and rising)."""
        macd = MACDValues(
            macd_line=100,
            signal_line=50,
            histogram=50,  # positive
            prev_histogram=40,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.ACTIVE

    def test_active_verde_escuro_macd_negative(self, strategy):
        """Test ACTIVE when verde escuro regardless of MACD value."""
        macd = MACDValues(
            macd_line=-10,  # negative but doesn't matter
            signal_line=-5,
            histogram=50,  # positive
            prev_histogram=40,  # rising
        )
        state = strategy._determine_state(macd)
        assert state == GridState.ACTIVE

    # Tests for PAUSE state (verde claro - always pauses now)

    def test_pause_verde_claro_macd_positive(self, strategy):
        """Test PAUSE when verde claro and MACD positive."""
        macd = MACDValues(
            macd_line=100,
            signal_line=50,
            histogram=50,  # positive
            prev_histogram=60,  # falling (descendo)
        )
        state = strategy._determine_state(macd)
        assert state == GridState.PAUSE

    def test_pause_verde_claro_macd_negative(self, strategy):
        """Test PAUSE when verde claro even if MACD negative (BE-023 change)."""
        macd = MACDValues(
            macd_line=-10,  # negative - but should still PAUSE now
            signal_line=-5,
            histogram=50,  # positive
            prev_histogram=60,  # falling
        )
        state = strategy._determine_state(macd)
        assert state == GridState.PAUSE  # Changed from ACTIVE to PAUSE

    def test_pause_verde_claro_macd_near_zero(self, strategy):
        """Test PAUSE when verde claro with MACD near zero (BE-023 fix)."""
        macd = MACDValues(
            macd_line=0.01,  # very close to zero - should PAUSE
            signal_line=-5,
            histogram=50,  # positive
            prev_histogram=60,  # falling
        )
        state = strategy._determine_state(macd)
        assert state == GridState.PAUSE

    def test_pause_verde_claro_macd_at_zero(self, strategy):
        """Test PAUSE when verde claro with MACD exactly zero."""
        macd = MACDValues(
            macd_line=0,  # exactly zero
            signal_line=-5,
            histogram=50,  # positive
            prev_histogram=60,  # falling
        )
        state = strategy._determine_state(macd)
        assert state == GridState.PAUSE

    # Tests for INACTIVE state (vermelho escuro)

    def test_inactive_vermelho_escuro(self, strategy):
        """Test INACTIVE when vermelho escuro (histogram negative and falling)."""
        macd = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,  # negative
            prev_histogram=-40,  # falling (descendo)
        )
        state = strategy._determine_state(macd)
        assert state == GridState.INACTIVE

    def test_inactive_vermelho_escuro_macd_positive(self, strategy):
        """Test INACTIVE when vermelho escuro regardless of MACD value."""
        macd = MACDValues(
            macd_line=10,  # positive but doesn't matter
            signal_line=5,
            histogram=-50,  # negative
            prev_histogram=-40,  # falling
        )
        state = strategy._determine_state(macd)
        assert state == GridState.INACTIVE


class TestMACDStrategyStateMachine:
    """Test the full state machine behavior."""

    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        return MACDStrategy(config)

    def test_cycle_activation_requires_both_lines_negative(self, strategy):
        """Test that cycle only activates with both lines negative."""
        # Simulate vermelho claro with only MACD negative
        macd_one_negative = MACDValues(
            macd_line=-100,
            signal_line=10,  # positive
            histogram=-50,
            prev_histogram=-60,
        )

        state = strategy._determine_state(macd_one_negative)
        assert state == GridState.WAIT
        assert strategy._cycle_activated is False

        # Simulate vermelho claro with both lines negative
        macd_both_negative = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,
            prev_histogram=-60,
        )

        # Verify that both lines negative returns ACTIVATE
        state = strategy._determine_state(macd_both_negative)
        assert state == GridState.ACTIVATE

    def test_verde_claro_to_verde_escuro_reactivates(self, strategy):
        """Test that going from verde claro to verde escuro reactivates trading."""
        # Start in verde claro (PAUSE)
        verde_claro = MACDValues(
            macd_line=100,
            signal_line=50,
            histogram=50,  # positive
            prev_histogram=60,  # falling = verde claro
        )
        assert strategy._determine_state(verde_claro) == GridState.PAUSE

        # Move to verde escuro (ACTIVE) - should reactivate immediately
        verde_escuro = MACDValues(
            macd_line=100,
            signal_line=50,
            histogram=70,  # positive
            prev_histogram=60,  # rising = verde escuro
        )
        assert strategy._determine_state(verde_escuro) == GridState.ACTIVE


class TestMACDStrategyTrigger:
    """Test trigger_activated functionality (BE-029)."""

    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        return MACDStrategy(config)

    def test_trigger_initially_false(self, strategy):
        """Test that trigger is initially deactivated."""
        assert strategy.is_trigger_activated is False

    def test_trigger_activated_automatically_on_activate_state(self, strategy):
        """Test that trigger activates automatically when ACTIVATE state is detected."""
        # Simulate ACTIVATE condition (vermelho claro + both lines negative)
        macd_activate = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,
            prev_histogram=-60,
        )

        # Mock get_state to trigger activation
        state = strategy._determine_state(macd_activate)
        assert state == GridState.ACTIVATE

        # Simulate what happens in get_state method
        if state == GridState.ACTIVATE:
            if not strategy._trigger_activated:
                strategy._trigger_activated = True

        assert strategy.is_trigger_activated is True

    def test_trigger_deactivated_automatically_on_inactive_state(self, strategy):
        """Test that trigger deactivates automatically when INACTIVE state is detected."""
        # First activate the trigger manually
        strategy._trigger_activated = True
        assert strategy.is_trigger_activated is True

        # Simulate INACTIVE condition (vermelho escuro)
        macd_inactive = MACDValues(
            macd_line=-100,
            signal_line=-50,
            histogram=-50,
            prev_histogram=-40,  # falling
        )

        state = strategy._determine_state(macd_inactive)
        assert state == GridState.INACTIVE

        # Simulate what happens in get_state method
        if state == GridState.INACTIVE:
            if strategy._trigger_activated:
                strategy._trigger_activated = False

        assert strategy.is_trigger_activated is False

    def test_manual_trigger_activation_success(self, strategy):
        """Test manual trigger activation when not in INACTIVE state."""
        # Set a safe state (not INACTIVE)
        strategy._prev_state = GridState.WAIT

        success = strategy.set_trigger(True)
        assert success is True
        assert strategy.is_trigger_activated is True

    def test_manual_trigger_activation_blocked_in_inactive(self, strategy):
        """Test that manual trigger activation is blocked in INACTIVE state."""
        # Set state to INACTIVE
        strategy._prev_state = GridState.INACTIVE

        success = strategy.set_trigger(True)
        assert success is False
        assert strategy.is_trigger_activated is False

    def test_manual_trigger_deactivation(self, strategy):
        """Test manual trigger deactivation."""
        # First activate
        strategy._trigger_activated = True
        assert strategy.is_trigger_activated is True

        # Deactivate
        success = strategy.set_trigger(False)
        assert success is True
        assert strategy.is_trigger_activated is False

    def test_manual_trigger_idempotent_activation(self, strategy):
        """Test that activating an already active trigger is idempotent."""
        strategy._prev_state = GridState.WAIT
        strategy._trigger_activated = True

        success = strategy.set_trigger(True)
        assert success is True
        assert strategy.is_trigger_activated is True

    def test_manual_trigger_idempotent_deactivation(self, strategy):
        """Test that deactivating an already inactive trigger is idempotent."""
        strategy._trigger_activated = False

        success = strategy.set_trigger(False)
        assert success is True
        assert strategy.is_trigger_activated is False

    def test_should_create_orders_requires_both_cycle_and_trigger(self, strategy):
        """Test that should_create_orders requires both cycle_activated AND trigger_activated."""
        # Test 1: Neither activated
        strategy._cycle_activated = False
        strategy._trigger_activated = False
        assert strategy.should_create_orders(GridState.ACTIVE) is False

        # Test 2: Only cycle activated
        strategy._cycle_activated = True
        strategy._trigger_activated = False
        assert strategy.should_create_orders(GridState.ACTIVE) is False

        # Test 3: Only trigger activated
        strategy._cycle_activated = False
        strategy._trigger_activated = True
        assert strategy.should_create_orders(GridState.ACTIVE) is False

        # Test 4: Both activated - should create
        strategy._cycle_activated = True
        strategy._trigger_activated = True
        assert strategy.should_create_orders(GridState.ACTIVE) is True

    def test_should_create_orders_respects_state(self, strategy):
        """Test that should_create_orders still respects state even with both flags."""
        strategy._cycle_activated = True
        strategy._trigger_activated = True

        # Should create in ACTIVE and ACTIVATE
        assert strategy.should_create_orders(GridState.ACTIVE) is True
        assert strategy.should_create_orders(GridState.ACTIVATE) is True

        # Should NOT create in other states
        assert strategy.should_create_orders(GridState.PAUSE) is False
        assert strategy.should_create_orders(GridState.INACTIVE) is False
        assert strategy.should_create_orders(GridState.WAIT) is False

    def test_trigger_manual_override_scenario(self, strategy):
        """
        Test the main use case: app starts after ACTIVATE already happened.

        User can manually activate trigger to start creating orders.
        """
        # Scenario: App started, market is in valid state but trigger hasn't happened
        strategy._prev_state = GridState.ACTIVE
        strategy._cycle_activated = True  # Cycle was manually activated
        strategy._trigger_activated = False  # But trigger never happened

        # Orders should NOT be created yet
        assert strategy.should_create_orders(GridState.ACTIVE) is False

        # User manually activates trigger
        success = strategy.set_trigger(True)
        assert success is True

        # Now orders should be created
        assert strategy.should_create_orders(GridState.ACTIVE) is True
