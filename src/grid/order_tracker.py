from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.utils.logger import orders_logger, trades_logger

if TYPE_CHECKING:
    from src.database.repositories.trade_repository import TradeRepository


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
    exchange_tp_order_id: str | None = None  # TP order ID from exchange
    trade_id: UUID | None = None  # FK to trades table (set when trade is persisted)

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

    def __init__(
        self,
        trade_repository: "TradeRepository | None" = None,
        account_id: UUID | None = None,
    ):
        self._orders: dict[str, TrackedOrder] = {}
        self._orders_by_price: dict[float, str] = {}  # price -> order_id mapping
        self._trades: list[TradeRecord] = []
        self._initial_pnl: float = 0.0  # PnL from exchange at startup
        self._trade_repository = trade_repository
        self._account_id = account_id

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

    def load_trade_history(self, trades: list) -> dict[str, Any]:
        """Load historical trades from database into memory.

        Args:
            trades: List of Trade model objects from database (must have status='CLOSED').

        Returns:
            Dict with loading statistics:
            - trades_loaded: Number of trades loaded
            - total_pnl: Total PnL from historical trades
            - win_rate: Win rate percentage
            - date_range: Tuple of (oldest_date, newest_date) or None

        Note:
            This method should be called during bot startup to restore
            trading history and statistics from the database.
        """
        if not trades:
            trades_logger.info("No historical trades to load")
            return {
                "trades_loaded": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "date_range": None,
            }

        # Convert Trade models to TradeRecords
        loaded_count = 0
        for trade in trades:
            # Skip if missing required fields
            if not all([trade.entry_price, trade.exit_price, trade.quantity, trade.pnl]):
                trades_logger.warning(
                    f"Skipping incomplete trade {trade.id}: missing required fields"
                )
                continue

            # Skip if missing timestamps
            if not trade.opened_at or not trade.closed_at:
                trades_logger.warning(f"Skipping trade {trade.id}: missing timestamps")
                continue

            trade_record = TradeRecord(
                entry_price=float(trade.entry_price),
                exit_price=float(trade.exit_price),
                quantity=float(trade.quantity),
                pnl=float(trade.pnl),
                entry_time=trade.opened_at,
                exit_time=trade.closed_at,
            )
            self._trades.append(trade_record)
            loaded_count += 1

        # Calculate statistics
        total_pnl = sum(t.pnl for t in self._trades)
        win_count = sum(1 for t in self._trades if t.pnl > 0)
        win_rate = (win_count / len(self._trades) * 100) if self._trades else 0.0

        # Get date range
        date_range = None
        if self._trades:
            dates = [t.exit_time for t in self._trades if t.exit_time]
            if dates:
                date_range = (min(dates), max(dates))

        stats = {
            "trades_loaded": loaded_count,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "date_range": date_range,
        }

        # Log summary
        if loaded_count > 0:
            trades_logger.info(
                f"Loaded {loaded_count} historical trades | "
                f"Total PnL: ${total_pnl:.2f} | "
                f"Win Rate: {win_rate:.1f}%"
            )
            if date_range:
                trades_logger.info(
                    f"History period: {date_range[0].strftime('%Y-%m-%d %H:%M')} → "
                    f"{date_range[1].strftime('%Y-%m-%d %H:%M')}"
                )

        return stats

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
        """Mark order as filled and create OPEN trade in database."""
        order = self._orders.get(order_id)
        if order:
            order.mark_filled()
            orders_logger.info(f"Order filled: {order_id} @ ${order.entry_price:,.2f}")

            # Persist OPEN trade to database (non-blocking)
            if self._trade_repository and self._account_id:
                self._schedule_open_trade_persistence(order)
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

        # Persist trade to database (async, non-blocking)
        if self._trade_repository and self._account_id:
            self._schedule_trade_persistence(order, exit_price, pnl, trade.pnl_percent)

        # Remove from tracking
        del self._orders[order_id]
        if order.entry_price in self._orders_by_price:
            del self._orders_by_price[order.entry_price]

        return trade

    def _schedule_open_trade_persistence(self, order: TrackedOrder) -> None:
        """Persist OPEN trade to database when order is filled (non-blocking)."""
        import asyncio

        async def _persist_open_trade() -> None:
            if not self._trade_repository or not self._account_id:
                return

            try:
                # Calculate TP percent
                tp_percent = (
                    ((order.tp_price - order.entry_price) / order.entry_price) * 100
                    if order.tp_price
                    else None
                )

                trade_data = {
                    "account_id": self._account_id,
                    "exchange_order_id": order.order_id,
                    "exchange_tp_order_id": order.exchange_tp_order_id,
                    "symbol": "BTC-USDT",
                    "side": "LONG",
                    "leverage": 10,
                    "entry_price": Decimal(str(order.entry_price)),
                    "exit_price": None,  # Not closed yet
                    "quantity": Decimal(str(order.quantity)),
                    "tp_price": Decimal(str(order.tp_price)) if order.tp_price else None,
                    "tp_percent": Decimal(str(tp_percent)) if tp_percent else None,
                    "pnl": None,  # Calculated when closed
                    "pnl_percent": None,
                    "trading_fee": Decimal("0"),
                    "funding_fee": Decimal("0"),
                    "status": "OPEN",  # KEY: status is OPEN
                    "grid_level": None,
                    "opened_at": order.created_at.replace(tzinfo=UTC),
                    "filled_at": (order.filled_at.replace(tzinfo=UTC) if order.filled_at else None),
                    "closed_at": None,  # Not closed yet
                }

                # Save and get trade_id
                trade_id = await self._trade_repository.save_trade(trade_data)
                order.trade_id = trade_id  # Store ID in TrackedOrder for later update

                trades_logger.info(
                    f"OPEN trade persisted: {order.order_id[:8]} (trade_id: {trade_id})"
                )
            except Exception as e:
                trades_logger.warning(f"Failed to persist OPEN trade: {e}")

        # Schedule task in background (fire and forget)
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_persist_open_trade())
        except RuntimeError:
            trades_logger.warning("No event loop running, skipping OPEN trade persistence")

    def _schedule_trade_persistence(
        self,
        order: TrackedOrder,
        exit_price: float,
        pnl: float,
        pnl_percent: float,
    ) -> None:
        """Schedule trade persistence to database (non-blocking)."""
        import asyncio

        async def _persist_trade() -> None:
            if not self._trade_repository or not self._account_id:
                return

            try:
                if order.trade_id:
                    # NUOVO: Update existing OPEN trade to CLOSED
                    await self._trade_repository.update_trade_exit(
                        trade_id=order.trade_id,
                        exit_price=Decimal(str(exit_price)),
                        pnl=Decimal(str(pnl)),
                        pnl_percent=Decimal(str(pnl_percent)),
                    )
                    trades_logger.info(
                        f"Trade updated to CLOSED: {order.order_id[:8]} (trade_id: {order.trade_id})"
                    )
                else:
                    # FALLBACK: Create CLOSED trade (backward compatible with trades without OPEN state)
                    # Calculate TP percent
                    tp_percent = (
                        ((order.tp_price - order.entry_price) / order.entry_price) * 100
                        if order.tp_price
                        else None
                    )

                    trade_data = {
                        "account_id": self._account_id,
                        "exchange_order_id": order.order_id,
                        "exchange_tp_order_id": order.exchange_tp_order_id,
                        "symbol": "BTC-USDT",
                        "side": "LONG",
                        "leverage": 10,
                        "entry_price": Decimal(str(order.entry_price)),
                        "exit_price": Decimal(str(exit_price)),
                        "quantity": Decimal(str(order.quantity)),
                        "tp_price": Decimal(str(order.tp_price)) if order.tp_price else None,
                        "tp_percent": Decimal(str(tp_percent)) if tp_percent else None,
                        "pnl": Decimal(str(pnl)),
                        "pnl_percent": Decimal(str(pnl_percent)),
                        "trading_fee": Decimal("0"),
                        "funding_fee": Decimal("0"),
                        "status": "CLOSED",
                        "grid_level": None,
                        "opened_at": order.created_at.replace(tzinfo=UTC),
                        "filled_at": (
                            order.filled_at.replace(tzinfo=UTC) if order.filled_at else None
                        ),
                        "closed_at": datetime.now(UTC),
                    }

                    await self._trade_repository.save_trade(trade_data)
                    trades_logger.info(
                        f"Trade persisted (CLOSED, no prior OPEN): {order.order_id[:8]}"
                    )
            except Exception as e:
                # Fallback: log warning but don't crash
                trades_logger.warning(
                    f"Failed to persist trade to database: {e}. Trade data kept in memory only."
                )

        # Schedule task in background (fire and forget)
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_persist_trade())
        except RuntimeError:
            # No event loop running, skip persistence
            trades_logger.warning("No event loop running, skipping trade persistence")

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
        anchor_value: float = 0,
    ) -> int:
        """
        Load existing positions from exchange into tracker.

        BUG-FIX-006: BingX consolidates multiple filled orders into a single position
        with an average price, but maintains individual take profit (TP) orders for
        each original fill. This method now derives individual positions from the
        TP orders rather than the consolidated position.

        For each TP order, we reverse-calculate the entry price:
            entry_price = tp_price / (1 + tp_percent / 100)

        This allows us to show N individual positions (one per TP order) instead
        of 1 consolidated position.

        Args:
            positions: List of positions from exchange (used only for validation)
            open_orders: List of open orders (TP orders are derived from here)
            tp_percent: Take profit percentage to reverse-calculate entry prices
            anchor_value: Grid anchor value for rounding (0 = no rounding)

        Returns:
            Number of positions loaded (count of TP orders)
        """
        # First, validate we have an actual position (sanity check)
        has_position = any(float(pos.get("positionAmt", 0)) != 0 for pos in positions)

        if not has_position:
            orders_logger.info("No open positions to load")
            return 0

        # Calculate multiplier for reverse entry price calculation
        tp_multiplier = 1 + (tp_percent / 100)

        loaded = 0
        for open_order in open_orders:
            order_type = open_order.get("type", "")

            # Only process TP orders
            if order_type not in ["TAKE_PROFIT_MARKET", "TAKE_PROFIT"]:
                continue

            tp_price = float(open_order.get("stopPrice", 0))
            quantity = float(open_order.get("origQty", 0))
            tp_order_id = str(open_order.get("orderId", ""))

            if tp_price <= 0 or quantity <= 0:
                continue

            # Reverse-calculate entry price from TP price
            entry_price = tp_price / tp_multiplier

            # Apply anchor rounding if configured
            if anchor_value > 0:
                entry_price = round(entry_price / anchor_value) * anchor_value
            else:
                entry_price = round(entry_price, 2)

            # Generate unique ID for this position (based on TP order ID)
            position_id = f"existing_tp_{tp_order_id}"

            # Skip if already tracked
            if position_id in self._orders:
                continue

            # Also skip if we already have an order at this entry price
            # (handles duplicate tracking)
            if entry_price in self._orders_by_price:
                continue

            # Create tracked order as FILLED
            order = TrackedOrder(
                order_id=position_id,
                entry_price=entry_price,
                tp_price=tp_price,
                quantity=quantity,
                status=OrderStatus.FILLED,
                filled_at=datetime.now(),
                exchange_tp_order_id=tp_order_id,
            )
            self._orders[position_id] = order
            self._orders_by_price[entry_price] = position_id

            orders_logger.info(
                f"Position loaded from TP: {quantity} BTC @ ${entry_price:,.2f} → TP ${tp_price:,.2f} (TP#{tp_order_id[:8]})"
            )
            loaded += 1

        if loaded > 0:
            orders_logger.info(f"Loaded {loaded} individual positions from TP orders")

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
