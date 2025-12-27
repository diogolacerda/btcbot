"""
Base interface for trading filters.

Filters determine whether orders should be created based on market conditions.
They can be enabled/disabled dynamically without bot restart.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FilterState:
    """State information for a filter."""

    enabled: bool
    description: str
    details: dict | None = None


class Filter(ABC):
    """
    Abstract base class for trading filters.

    Filters implement the strategy pattern to determine if order creation
    should be allowed based on market conditions.

    All filters are enabled by default on startup.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize filter.

        Args:
            name: Unique identifier for this filter (e.g., "macd")
            description: Human-readable description (e.g., "MACD Crossover")
        """
        self._name = name
        self._description = description
        self._enabled = True  # Enabled by default

    @property
    def name(self) -> str:
        """Get filter unique name."""
        return self._name

    @property
    def description(self) -> str:
        """Get filter description."""
        return self._description

    @property
    def enabled(self) -> bool:
        """Check if filter is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable this filter."""
        self._enabled = True

    def disable(self) -> None:
        """Disable this filter."""
        self._enabled = False

    def set_enabled(self, enabled: bool) -> None:
        """
        Set filter enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled

    @abstractmethod
    def should_allow_trade(self) -> bool:
        """
        Check if trade should be allowed based on filter logic.

        Returns:
            True if trade is allowed, False otherwise
        """
        pass

    @abstractmethod
    def get_state(self) -> FilterState:
        """
        Get current filter state with details.

        Returns:
            FilterState with enabled status and additional details
        """
        pass
