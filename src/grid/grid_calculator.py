from dataclasses import dataclass

from config import GridConfig, SpacingType
from src.utils.helpers import round_price


@dataclass
class GridLevel:
    """Represents a single grid level with entry and take profit prices."""

    entry_price: float
    tp_price: float
    level_index: int

    def __str__(self) -> str:
        return (
            f"Level {self.level_index}: Entry ${self.entry_price:,.2f} → TP ${self.tp_price:,.2f}"
        )


class GridCalculator:
    """
    Calculates grid levels based on current price and configuration.

    The grid creates LONG orders below the current price, each with its own take profit.
    """

    def __init__(self, config: GridConfig):
        self.spacing_type = config.spacing_type
        self.spacing_value = config.spacing_value
        self.range_percent = config.range_percent
        self.tp_percent = config.take_profit_percent
        self.max_total_orders = config.max_total_orders

    def calculate_spacing(self, reference_price: float) -> float:
        """
        Calculate the spacing between grid levels.

        Args:
            reference_price: Current price to calculate percentage spacing from

        Returns:
            Spacing value in price units
        """
        if self.spacing_type == SpacingType.FIXED:
            return self.spacing_value
        else:
            return reference_price * (self.spacing_value / 100)

    def calculate_min_price(self, current_price: float) -> float:
        """
        Calculate the minimum price for grid orders (range limit).

        Args:
            current_price: Current market price

        Returns:
            Minimum price for grid orders
        """
        return current_price * (1 - self.range_percent / 100)

    def calculate_tp_price(self, entry_price: float) -> float:
        """
        Calculate take profit price for an entry.

        Args:
            entry_price: Entry price of the order

        Returns:
            Take profit price
        """
        return entry_price * (1 + self.tp_percent / 100)

    def calculate_levels(
        self,
        current_price: float,
        existing_levels: list[float] | None = None,
        max_levels: int | None = None,
    ) -> list[GridLevel]:
        """
        Calculate all grid levels for the current price.

        Creates evenly spaced orders below the current price within the configured range.

        Args:
            current_price: Current market price
            existing_levels: List of existing entry prices (to avoid duplicates)
            max_levels: Override for max levels (used for dynamic slot calculation)

        Returns:
            List of GridLevel objects
        """
        existing_levels = existing_levels or []
        existing_set = {round_price(p) for p in existing_levels}

        min_price = self.calculate_min_price(current_price)

        # Use provided max_levels or fall back to max_total_orders
        effective_max = max_levels if max_levels is not None else self.max_total_orders

        levels: list[GridLevel] = []
        level_index = 1

        # Evenly spaced orders
        spacing = self.calculate_spacing(current_price)
        price = current_price - spacing

        while price >= min_price and len(levels) < effective_max:
            rounded_price = round_price(price)

            if rounded_price not in existing_set:
                tp_price = round_price(self.calculate_tp_price(rounded_price))
                levels.append(
                    GridLevel(
                        entry_price=rounded_price,
                        tp_price=tp_price,
                        level_index=level_index,
                    )
                )

            level_index += 1
            price -= spacing

        return levels

    def get_levels_to_create(
        self,
        current_price: float,
        existing_orders: list[dict],
        filled_orders_count: int = 0,
    ) -> list[GridLevel]:
        """
        Get grid levels that need to be created.

        The total number of orders is limited by:
        available_slots = max_total_orders - filled_orders_count - pending_limit_orders

        Args:
            current_price: Current market price
            existing_orders: List of existing orders with 'price' key
            filled_orders_count: Number of filled orders awaiting TP (count of TP orders)

        Returns:
            List of GridLevel objects to create
        """
        min_price = self.calculate_min_price(current_price)

        # Count only orders within range
        orders_in_range = [o for o in existing_orders if float(o.get("price", 0)) >= min_price]
        existing_prices = [float(o.get("price", 0)) for o in existing_orders]
        levels = self.calculate_levels(current_price, existing_prices)

        # Limit based on orders IN RANGE + filled orders (BE-008)
        remaining_slots = max(0, self.max_total_orders - len(orders_in_range) - filled_orders_count)
        return levels[:remaining_slots]

    def get_orders_to_cancel(
        self,
        current_price: float,
        existing_orders: list[dict],
        filled_orders_count: int = 0,
    ) -> list[dict]:
        """
        Get orders that are outside the current range and should be cancelled.

        Args:
            current_price: Current market price
            existing_orders: List of existing orders
            filled_orders_count: Number of filled orders awaiting TP (count of TP orders)

        Returns:
            List of orders to cancel
        """
        if not existing_orders:
            return []

        min_price = self.calculate_min_price(current_price)
        orders_to_cancel = []

        # Filter LIMIT orders only (not TPs)
        limit_orders = [o for o in existing_orders if o.get("type") == "LIMIT"]

        # Cancel orders outside range (below min_price)
        for order in limit_orders:
            order_price = float(order.get("price", 0))
            if order_price < min_price:
                orders_to_cancel.append(order)

        return orders_to_cancel

    def get_grid_summary(self, current_price: float, open_positions_count: int = 0) -> dict:
        """
        Get summary of grid configuration.

        Args:
            current_price: Current market price
            open_positions_count: Number of open positions (for available slots calc)

        Returns:
            Dictionary with grid summary
        """
        spacing = self.calculate_spacing(current_price)
        min_price = self.calculate_min_price(current_price)
        levels_by_range = int((current_price - min_price) / spacing)
        available_slots = max(0, self.max_total_orders - open_positions_count)
        max_levels = min(levels_by_range, available_slots)

        return {
            "current_price": current_price,
            "min_price": min_price,
            "spacing": spacing,
            "spacing_type": self.spacing_type.value,
            "range_percent": self.range_percent,
            "tp_percent": self.tp_percent,
            "max_total_orders": self.max_total_orders,
            "open_positions": open_positions_count,
            "available_slots": available_slots,
            "max_levels": max_levels,
        }
