from dataclasses import dataclass

from config import GridAnchorMode, GridConfig, SpacingType
from src.utils.helpers import anchor_price, round_price


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
        self.anchor_mode = config.anchor_mode
        self.anchor_value = config.anchor_value

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

    def get_anchor_level(self, price: float) -> float:
        """
        Get the anchor level for a given price.

        Returns the nearest anchor value below the price when anchor mode is enabled.
        For example, with anchor_value=100 and price=88150, returns 88100.

        Args:
            price: Price to anchor

        Returns:
            Anchored price (or original price if anchor mode is disabled)
        """
        if self.anchor_mode == GridAnchorMode.NONE:
            return price

        return anchor_price(price, self.anchor_value)

    def calculate_levels(
        self,
        current_price: float,
        existing_levels: list[float] | None = None,
        max_levels: int | None = None,
    ) -> list[GridLevel]:
        """
        Calculate all grid levels for the current price.

        When anchor mode is enabled (HUNDRED), creates orders at clean price levels
        (e.g., $88000, $87900, etc) instead of arbitrary prices.

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

        if self.anchor_mode == GridAnchorMode.NONE:
            # Original behavior: evenly spaced orders
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

        else:
            # Anchored mode: create orders at anchor levels (e.g., hundreds)
            # Start from the anchor level just below current price
            current_anchor = self.get_anchor_level(current_price)

            # If current price is exactly at an anchor level, start from the one below
            if abs(current_anchor - current_price) < 0.01:
                current_anchor -= self.anchor_value

            price = current_anchor

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
                price -= self.anchor_value  # Move to next anchor level

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

        if self.anchor_mode == GridAnchorMode.NONE:
            # Original behavior: count only orders within range
            orders_in_range = [o for o in existing_orders if float(o.get("price", 0)) >= min_price]
            existing_prices = [float(o.get("price", 0)) for o in existing_orders]
            levels = self.calculate_levels(current_price, existing_prices)

            # Limit based on orders IN RANGE + filled orders (BE-008)
            remaining_slots = max(
                0, self.max_total_orders - len(orders_in_range) - filled_orders_count
            )
            return levels[:remaining_slots]

        else:
            # Anchored mode: count LIMIT orders only
            limit_orders = [o for o in existing_orders if o.get("type") == "LIMIT"]
            existing_prices = [float(o.get("price", 0)) for o in limit_orders]
            levels = self.calculate_levels(current_price, existing_prices)

            # Limit based on total LIMIT orders + filled orders (BE-008)
            remaining_slots = max(
                0, self.max_total_orders - len(limit_orders) - filled_orders_count
            )
            return levels[:remaining_slots]

    def get_orders_to_cancel(
        self,
        current_price: float,
        existing_orders: list[dict],
        filled_orders_count: int = 0,
    ) -> list[dict]:
        """
        Get orders that are outside the current range and should be cancelled.

        In anchored mode, this maintains exactly N orders (max_total_orders - filled_orders)
        by canceling the furthest orders when price rises and new anchor levels become available.

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

        # Calculate available slots for LIMIT orders (BE-008)
        max_limit_orders = max(0, self.max_total_orders - filled_orders_count)

        if self.anchor_mode == GridAnchorMode.NONE:
            # Original behavior: cancel orders outside range
            for order in existing_orders:
                order_price = float(order.get("price", 0))
                if order_price < min_price:
                    orders_to_cancel.append(order)

        else:
            # Anchored mode: maintain N orders closest to current price
            # Filter LIMIT orders only (not TPs)
            limit_orders = [o for o in existing_orders if o.get("type") == "LIMIT"]

            if not limit_orders:
                return []

            # Sort orders by price (descending - highest first)
            sorted_orders = sorted(
                limit_orders, key=lambda o: float(o.get("price", 0)), reverse=True
            )

            # Cancel if we have more than available slots (BE-008)
            if len(sorted_orders) > max_limit_orders:
                orders_to_cancel = sorted_orders[max_limit_orders:]

            # Also cancel any orders below min_price (outside range)
            for order in sorted_orders:
                order_price = float(order.get("price", 0))
                if order_price < min_price and order not in orders_to_cancel:
                    orders_to_cancel.append(order)

            # If we have exactly max slots, check if new anchor levels are available
            # and cancel the furthest order to make room
            if len(sorted_orders) == max_limit_orders and len(orders_to_cancel) == 0:
                # Calculate the highest anchor level below current price
                anchor_below_price = self.get_anchor_level(current_price)
                if abs(anchor_below_price - current_price) < 0.01:
                    anchor_below_price -= self.anchor_value

                # Check if this anchor level is missing from existing orders
                existing_prices = {float(o.get("price", 0)) for o in sorted_orders}

                if anchor_below_price not in existing_prices and anchor_below_price >= min_price:
                    # Cancel the furthest (lowest) order to make room
                    orders_to_cancel.append(sorted_orders[-1])

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
