"""
MACD filter for grid trading.

Wraps the existing MACDStrategy to provide filter functionality.
Determines if orders should be created based on MACD indicators.
"""

from src.filters.base import Filter, FilterState
from src.strategy.macd_strategy import GridState, MACDStrategy
from src.utils.logger import main_logger


class MACDFilter(Filter):
    """
    Filter based on MACD strategy.

    When enabled:
    - Uses MACD strategy to determine if orders should be created
    - Respects GridState (ACTIVATE, ACTIVE allow trades; others don't)
    - Enforces cycle activation logic

    When disabled:
    - Always allows trades (bypasses MACD logic)
    """

    def __init__(self, strategy: MACDStrategy, *, enabled: bool | None = None):
        """
        Initialize MACD filter.

        Args:
            strategy: Existing MACDStrategy instance
            enabled: Initial enabled state. If None, defaults to True.
        """
        super().__init__(
            name="macd",
            description="MACD Crossover Strategy",
        )
        self._strategy = strategy
        self._current_state = GridState.WAIT
        self._on_state_change_callback = None

        # Set initial enabled state if provided
        if enabled is not None:
            self._enabled = enabled

    def set_on_state_change_callback(self, callback) -> None:
        """
        Set callback to be called when MACD state changes.

        Args:
            callback: Callable to invoke on state change (old_state, new_state)
        """
        self._on_state_change_callback = callback

    async def set_current_state(self, state: GridState) -> None:
        """
        Update current MACD state.

        This should be called by GridManager after calculating state.

        Args:
            state: Current GridState from MACD calculation
        """
        old_state = self._current_state
        self._current_state = state

        # Trigger callback on state change
        if old_state != state and self._on_state_change_callback:
            await self._on_state_change_callback(old_state, state)

    def should_allow_trade(self) -> bool:
        """
        Check if trade should be allowed based on MACD.

        When filter is disabled, always returns True.
        When filter is enabled, uses MACD strategy logic.

        Returns:
            True if trade is allowed, False otherwise
        """
        if not self.enabled:
            return True

        # Use strategy's should_create_orders logic
        return self._strategy.should_create_orders(self._current_state)

    def get_state(self) -> FilterState:
        """
        Get current filter state with MACD details.

        Returns:
            FilterState with MACD indicators and state
        """
        details = {
            "current_state": self._current_state.value,
            "cycle_activated": self._strategy.is_cycle_activated,
            "trigger_activated": self._strategy.is_trigger_activated,
            "state_description": self._strategy.get_state_description(self._current_state),
        }

        return FilterState(
            enabled=self.enabled,
            description=self.description,
            details=details,
        )

    def manual_activate(self) -> bool:
        """
        Manually activate the MACD cycle.

        Returns:
            True if activated successfully, False if not allowed
        """
        success = self._strategy.manual_activate()
        if success:
            main_logger.info("MACD filter cycle manually activated")
        return success

    def manual_deactivate(self) -> None:
        """Manually deactivate the MACD cycle."""
        self._strategy.manual_deactivate()
        main_logger.info("MACD filter cycle manually deactivated")

    def set_trigger(self, activated: bool) -> bool:
        """
        Manually set trigger state.

        Args:
            activated: True to activate trigger, False to deactivate

        Returns:
            True if set successfully, False if not allowed
        """
        success = self._strategy.set_trigger(activated)
        if success:
            action = "activated" if activated else "deactivated"
            main_logger.info(f"MACD filter trigger manually {action}")
        return success

    def sync_with_strategy(self) -> None:
        """
        Sync filter enabled state with MACDStrategy.

        After MACDStrategy loads config from DB (via load_config_from_db()),
        this method syncs the filter's enabled state with the strategy's
        is_macd_enabled property.

        Should be called after strategy.load_config_from_db() completes.
        """
        strategy_enabled = self._strategy.is_macd_enabled
        if self._enabled != strategy_enabled:
            old_state = "enabled" if self._enabled else "disabled"
            new_state = "enabled" if strategy_enabled else "disabled"
            self._enabled = strategy_enabled
            main_logger.info(f"MACD filter synced with strategy: {old_state} -> {new_state}")
