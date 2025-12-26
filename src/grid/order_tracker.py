from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.utils.logger import orders_logger, trades_logger


class OrderStatus(Enum):
    """Status of a grid order."""

    PENDING = "pending"  # Order placed, waiting to be filled
    FILLED = "filled"  # Order filled, position opened
    TP_HIT = "tp_hit"  # Take profit hit, position closed
    CANCELLED = "cancelled"  # Order cancelled


@dataclass
class TrackedOrder:
    """Represents a tracked grid order."""

    order_id: str
    entry_price: float
    tp_price: float
    quantity: float
    status: OrderStatus
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: datetime | None = None
    closed_at: datetime | None = None
    pnl: float | None = None

    def mark_filled(self) -> None:
        """Mark order as filled."""
        self.status = OrderStatus.FILLED
        self.filled_at = datetime.now()

    def mark_tp_hit(self, pnl: float) -> None:
        """Mark order as take profit hit."""
        self.status = OrderStatus.TP_HIT
        self.closed_at = datetime.now()
        self.pnl = pnl

    def mark_cancelled(self) -> None:
        """Mark order as cancelled."""
        self.status = OrderStatus.CANCELLED


@dataclass
class TradeRecord:
    """Record of a completed trade."""

    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    entry_time: datetime
    exit_time: datetime

    @property
    def pnl_percent(self) -> float:
        return (self.pnl / (self.entry_price * self.quantity)) * 100


class OrderTracker:
    """
    Tracks the state of all grid orders in memory.

    Maintains:
    - Pending orders (LIMIT orders waiting to be filled)
    - Filled orders (positions that are open)
    - Completed trades (for statistics)
    """

    def __init__(self):
        self._orders: dict[str, TrackedOrder] = {}
        self._orders_by_price: dict[float, str] = {}  # price -> order_id mapping
        self._trades: list[TradeRecord] = []
        self._initial_pnl: float = 0.0  # PnL from exchange at startup

    @property
    def pending_orders(self) -> list[TrackedOrder]:
        """Get all pending orders."""
        return [o for o in self._orders.values() if o.status == OrderStatus.PENDING]

    @property
    def filled_orders(self) -> list[TrackedOrder]:
        """Get all filled orders (open positions)."""
        return [o for o in self._orders.values() if o.status == OrderStatus.FILLED]

    @property
    def pending_count(self) -> int:
        """Count of pending orders."""
        return len(self.pending_orders)

    @property
    def position_count(self) -> int:
        """Count of open positions."""
        return len(self.filled_orders)

    @property
    def total_trades(self) -> int:
        """Total number of completed trades."""
        return len(self._trades)

    @property
    def total_pnl(self) -> float:
        """Total PnL from all trades (initial from exchange + session trades)."""
        return self._initial_pnl + sum(t.pnl for t in self._trades)

    def set_initial_pnl(self, pnl: float) -> None:
        """Set initial PnL from exchange."""
        self._initial_pnl = pnl
        orders_logger.info(f"PnL inicial da plataforma: ${pnl:.2f}")

    @property
    def win_rate(self) -> float:
        """Win rate percentage."""
        if not self._trades:
            return 0.0
        wins = sum(1 for t in self._trades if t.pnl > 0)
        return (wins / len(self._trades)) * 100

    def add_order(
        self,
        order_id: str,
        entry_price: float,
        tp_price: float,
        quantity: float,
    ) -> TrackedOrder:
        """Add a new order to tracking."""
        order = TrackedOrder(
            order_id=order_id,
            entry_price=entry_price,
            tp_price=tp_price,
            quantity=quantity,
            status=OrderStatus.PENDING,
        )
        self._orders[order_id] = order
        self._orders_by_price[entry_price] = order_id

        orders_logger.debug(f"Order tracked: {order_id} @ ${entry_price:,.2f}")
        return order

    def get_order(self, order_id: str) -> TrackedOrder | None:
        """Get order by ID."""
        return self._orders.get(order_id)

    def get_order_by_price(self, price: float) -> TrackedOrder | None:
        """Get order by entry price."""
        order_id = self._orders_by_price.get(price)
        if order_id:
            return self._orders.get(order_id)
        return None

    def order_filled(self, order_id: str) -> TrackedOrder | None:
        """Mark order as filled."""
        order = self._orders.get(order_id)
        if order:
            order.mark_filled()
            orders_logger.info(
                f"Order filled: {order_id} @ ${order.entry_price:,.2f}"
            )
        return order

    def order_tp_hit(self, order_id: str, exit_price: float) -> TradeRecord | None:
        """Mark order as take profit hit and record trade."""
        order = self._orders.get(order_id)
        if not order:
            return None

        pnl = (exit_price - order.entry_price) * order.quantity
        order.mark_tp_hit(pnl)

        trade = TradeRecord(
            entry_price=order.entry_price,
            exit_price=exit_price,
            quantity=order.quantity,
            pnl=pnl,
            entry_time=order.filled_at or order.created_at,
            exit_time=datetime.now(),
        )
        self._trades.append(trade)

        trades_logger.info(
            f"TP Hit: ${order.entry_price:,.2f} → ${exit_price:,.2f} | "
            f"PnL: +${pnl:.2f} ({trade.pnl_percent:.2f}%)"
        )

        # Remove from tracking
        del self._orders[order_id]
        if order.entry_price in self._orders_by_price:
            del self._orders_by_price[order.entry_price]

        return trade

    def cancel_order(self, order_id: str) -> TrackedOrder | None:
        """Mark order as cancelled and remove from tracking."""
        order = self._orders.get(order_id)
        if order:
            order.mark_cancelled()
            del self._orders[order_id]
            if order.entry_price in self._orders_by_price:
                del self._orders_by_price[order.entry_price]
            orders_logger.info(f"Order cancelled: {order_id}")
        return order

    def has_order_at_price(self, price: float) -> bool:
        """Check if there's already an order at this price."""
        return price in self._orders_by_price

    def get_all_entry_prices(self) -> list[float]:
        """Get all entry prices of current orders."""
        return list(self._orders_by_price.keys())

    def clear_all(self) -> None:
        """Clear all tracked orders."""
        self._orders.clear()
        self._orders_by_price.clear()
        orders_logger.info("All tracked orders cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get trading statistics."""
        return {
            "pending_orders": self.pending_count,
            "open_positions": self.position_count,
            "total_trades": self.total_trades,
            "total_pnl": self.total_pnl,
            "win_rate": self.win_rate,
            "recent_trades": self._trades[-10:] if self._trades else [],
        }

    def load_existing_positions(
        self,
        positions: list[dict],
        open_orders: list[dict],
        tp_percent: float,
    ) -> int:
        """
        Load existing positions from exchange into tracker.

        Called at startup to track positions that were opened before the app started.

        Args:
            positions: List of positions from exchange
            open_orders: List of open orders (to find existing TPs)
            tp_percent: Take profit percentage to calculate TP price (fallback)

        Returns:
            Number of positions loaded
        """
        # Find existing TP orders
        existing_tps = {}
        for order in open_orders:
            order_type = order.get("type", "")
            if order_type in ["TAKE_PROFIT_MARKET", "TAKE_PROFIT"]:
                stop_price = float(order.get("stopPrice", 0))
                qty = float(order.get("origQty", 0))
                if stop_price > 0:
                    existing_tps[qty] = stop_price

        loaded = 0
        for pos in positions:
            # BingX position fields
            position_amt = float(pos.get("positionAmt", 0))
            if position_amt == 0:
                continue  # Skip empty positions

            avg_price = float(pos.get("avgPrice", 0))
            if avg_price == 0:
                continue

            # Generate a unique ID for this position
            position_id = f"existing_{pos.get('symbol', 'unknown')}_{avg_price}"

            # Skip if already tracked
            if position_id in self._orders:
                continue

            # Try to find existing TP for this position quantity
            tp_price = existing_tps.get(abs(position_amt))
            if not tp_price:
                # Fallback: calculate TP based on config
                tp_price = avg_price * (1 + tp_percent / 100)
                tp_source = "calculado"
            else:
                tp_source = "existente"

            # Create tracked order as FILLED
            order = TrackedOrder(
                order_id=position_id,
                entry_price=avg_price,
                tp_price=tp_price,
                quantity=abs(position_amt),
                status=OrderStatus.FILLED,
                filled_at=datetime.now(),
            )
            self._orders[position_id] = order
            self._orders_by_price[avg_price] = position_id

            orders_logger.info(
                f"Posição existente carregada: {abs(position_amt)} BTC @ ${avg_price:,.2f} → TP ${tp_price:,.2f} ({tp_source})"
            )
            loaded += 1

        return loaded

    def load_existing_orders(
        self,
        orders: list[dict],
        tp_percent: float,
    ) -> int:
        """
        Load existing pending orders from exchange into tracker.

        Args:
            orders: List of open orders from exchange
            tp_percent: Take profit percentage to calculate TP price

        Returns:
            Number of orders loaded
        """
        loaded = 0
        for order_data in orders:
            order_id = str(order_data.get("orderId", ""))
            if not order_id:
                continue

            # Skip if already tracked
            if order_id in self._orders:
                continue

            price = float(order_data.get("price", 0))
            quantity = float(order_data.get("origQty", 0))

            if price == 0 or quantity == 0:
                continue

            # Calculate TP price
            tp_price = price * (1 + tp_percent / 100)

            # Create tracked order as PENDING
            order = TrackedOrder(
                order_id=order_id,
                entry_price=price,
                tp_price=tp_price,
                quantity=quantity,
                status=OrderStatus.PENDING,
            )
            self._orders[order_id] = order
            self._orders_by_price[price] = order_id

            orders_logger.info(
                f"Ordem existente carregada: {order_id} @ ${price:,.2f} → TP ${tp_price:,.2f}"
            )
            loaded += 1

        return loaded

    def sync_with_exchange(
        self,
        exchange_orders: list[dict],
        exchange_positions: list[dict],
    ) -> None:
        """
        Sync local state with exchange data.

        Args:
            exchange_orders: List of orders from exchange
            exchange_positions: List of positions from exchange
        """
        exchange_order_ids = {str(o.get("orderId")) for o in exchange_orders}
        local_order_ids = set(self._orders.keys())

        # Remove orders that no longer exist on exchange
        for order_id in local_order_ids - exchange_order_ids:
            order = self._orders.get(order_id)
            if order and order.status == OrderStatus.PENDING:
                # Order was filled or cancelled on exchange
                order.mark_filled()
                orders_logger.info(f"Order synced as filled: {order_id}")
