import time
from decimal import Decimal, ROUND_DOWN


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
