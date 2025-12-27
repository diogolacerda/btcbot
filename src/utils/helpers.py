import time
from decimal import ROUND_DOWN, Decimal


def current_timestamp_ms() -> int:
    """Return current timestamp in milliseconds."""
    return int(time.time() * 1000)


def round_price(price: float, tick_size: float = 0.1) -> float:
    """Round price to the nearest tick size."""
    decimal_price = Decimal(str(price))
    decimal_tick = Decimal(str(tick_size))
    return float(decimal_price.quantize(decimal_tick, rounding=ROUND_DOWN))


def round_quantity(quantity: float, step_size: float = 0.001) -> float:
    """Round quantity to the nearest step size."""
    decimal_qty = Decimal(str(quantity))
    decimal_step = Decimal(str(step_size))
    return float(decimal_qty.quantize(decimal_step, rounding=ROUND_DOWN))


def calculate_pnl(entry_price: float, current_price: float, quantity: float, side: str) -> float:
    """Calculate unrealized PnL for a position."""
    if side.upper() == "LONG":
        return (current_price - entry_price) * quantity
    else:
        return (entry_price - current_price) * quantity


def format_price(price: float) -> str:
    """Format price with comma separators."""
    return f"${price:,.2f}"


def format_pnl(pnl: float) -> str:
    """Format PnL with sign and color indicator."""
    sign = "+" if pnl >= 0 else ""
    return f"{sign}${pnl:.2f}"


def anchor_price(price: float, anchor_value: float) -> float:
    """
    Round price to the nearest anchor value.

    Used for grid anchoring to create orders at clean price levels.

    Args:
        price: Price to anchor
        anchor_value: Anchor value (e.g., 100 for hundreds, 1000 for thousands)

    Returns:
        Price rounded down to nearest anchor value

    Examples:
        >>> anchor_price(88050, 100)
        88000.0
        >>> anchor_price(87932.5, 100)
        87900.0
        >>> anchor_price(88150, 100)
        88100.0
    """
    if anchor_value <= 0:
        return price

    return float(int(price / anchor_value) * anchor_value)
