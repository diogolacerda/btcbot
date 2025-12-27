"""
Pluggable filter system for grid trading.

Filters can be enabled/disabled dynamically via API without restarting the bot.
When all filters are disabled, the bot creates orders based solely on price and MAX_ORDERS.
"""

from src.filters.base import Filter
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry

__all__ = ["Filter", "FilterRegistry", "MACDFilter"]
