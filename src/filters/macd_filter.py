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

    def __init__(self, strategy: MACDStrategy):
        """
        Initialize MACD filter.

        Args:
            strategy: Existing MACDStrategy instance
        """
        super().__init__(
            name="macd",
            description="MACD Crossover Strategy",
        )
        self._strategy = strategy
        self._current_state = GridState.WAIT

    def set_current_state(self, state: GridState) -> None:
        """
        Update current MACD state.

        This should be called by GridManager after calculating state.

        Args:
            state: Current GridState from MACD calculation
        """
        self._current_state = state

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
