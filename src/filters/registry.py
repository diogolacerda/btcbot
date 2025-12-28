"""
Global registry for managing trading filters.

Provides centralized control over all filters with enable/disable capabilities.
Implements singleton pattern to ensure single source of truth.
"""

from typing import Any

from src.filters.base import Filter
from src.utils.logger import main_logger


class FilterRegistry:
    """
    Singleton registry for managing all trading filters.

    Filters can be:
    - Registered at startup
    - Enabled/disabled individually
    - Bulk enabled/disabled
    - Queried for state

    When no filters are enabled, trades are allowed based only on
    price levels and MAX_ORDERS configuration.
    """

    _instance: "FilterRegistry | None" = None

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry (only once)."""
        if self._initialized:
            return

        self._filters: dict[str, Filter] = {}
        self._initialized = True
        self._on_filter_change_callback: Any | None = None
        main_logger.info("FilterRegistry initialized")

    def register(self, filter_instance: Filter) -> None:
        """
        Register a new filter.

        Args:
            filter_instance: Filter instance to register

        Raises:
            ValueError: If filter with same name already registered
        """
        if filter_instance.name in self._filters:
            raise ValueError(f"Filter '{filter_instance.name}' already registered")

        self._filters[filter_instance.name] = filter_instance
        main_logger.info(
            f"Filter registered: {filter_instance.name} - {filter_instance.description}"
        )

    def get_filter(self, name: str) -> Filter | None:
        """
        Get filter by name.

        Args:
            name: Filter name

        Returns:
            Filter instance or None if not found
        """
        return self._filters.get(name)

    def set_on_filter_change_callback(self, callback: Any) -> None:
        """
        Set callback to be called when filter state changes.

        Args:
            callback: Callable to invoke on filter state change
        """
        self._on_filter_change_callback = callback

    def enable_filter(self, name: str) -> bool:
        """
        Enable a specific filter.

        Args:
            name: Filter name

        Returns:
            True if enabled successfully, False if filter not found
        """
        filter_instance = self._filters.get(name)
        if not filter_instance:
            main_logger.warning(f"Cannot enable unknown filter: {name}")
            return False

        was_enabled = filter_instance.enabled
        filter_instance.enable()
        main_logger.info(f"Filter enabled: {name}")

        # Trigger callback if state changed
        if not was_enabled and self._on_filter_change_callback:
            self._on_filter_change_callback(name, "enabled")

        return True

    def disable_filter(self, name: str) -> bool:
        """
        Disable a specific filter.

        Args:
            name: Filter name

        Returns:
            True if disabled successfully, False if filter not found
        """
        filter_instance = self._filters.get(name)
        if not filter_instance:
            main_logger.warning(f"Cannot disable unknown filter: {name}")
            return False

        was_enabled = filter_instance.enabled
        filter_instance.disable()
        main_logger.info(f"Filter disabled: {name}")

        # Trigger callback if state changed
        if was_enabled and self._on_filter_change_callback:
            self._on_filter_change_callback(name, "disabled")

        return True

    def enable_all(self) -> None:
        """Enable all registered filters."""
        any_changed = False
        for filter_instance in self._filters.values():
            if not filter_instance.enabled:
                any_changed = True
            filter_instance.enable()
        main_logger.info("All filters enabled")

        # Trigger callback if any filter changed
        if any_changed and self._on_filter_change_callback:
            self._on_filter_change_callback("all", "enabled")

    def disable_all(self) -> None:
        """Disable all registered filters."""
        any_changed = False
        for filter_instance in self._filters.values():
            if filter_instance.enabled:
                any_changed = True
            filter_instance.disable()
        main_logger.info("All filters disabled")

        # Trigger callback if any filter changed
        if any_changed and self._on_filter_change_callback:
            self._on_filter_change_callback("all", "disabled")

    def should_allow_trade(self) -> bool:
        """
        Check if trade should be allowed based on all enabled filters.

        If no filters are enabled, returns True (allow trade).
        If any enabled filter returns False, returns False (deny trade).

        Returns:
            True if all enabled filters allow trade, False otherwise
        """
        enabled_filters = [f for f in self._filters.values() if f.enabled]

        # No filters enabled = allow trade
        if not enabled_filters:
            return True

        # All enabled filters must allow trade
        for filter_instance in enabled_filters:
            if not filter_instance.should_allow_trade():
                return False

        return True

    def get_all_states(self) -> dict[str, Any]:
        """
        Get state of all registered filters.

        Returns:
            Dict with filter states and summary info
        """
        filters_state = {}
        for name, filter_instance in self._filters.items():
            state = filter_instance.get_state()
            filters_state[name] = {
                "enabled": state.enabled,
                "description": state.description,
                "details": state.details or {},
            }

        all_enabled = all(f.enabled for f in self._filters.values())
        any_enabled = any(f.enabled for f in self._filters.values())

        return {
            "filters": filters_state,
            "all_enabled": all_enabled,
            "any_enabled": any_enabled,
            "total_count": len(self._filters),
            "enabled_count": sum(1 for f in self._filters.values() if f.enabled),
        }

    def list_filters(self) -> list[str]:
        """
        Get list of all registered filter names.

        Returns:
            List of filter names
        """
        return list(self._filters.keys())

    def clear(self) -> None:
        """Clear all registered filters (mainly for testing)."""
        self._filters.clear()
        main_logger.info("FilterRegistry cleared")
