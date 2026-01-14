"""Dynamic Take Profit Manager based on funding rate."""

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from config import DynamicTPConfig
from src.utils.logger import orders_logger

if TYPE_CHECKING:
    from src.client.bingx_client import BingXClient
    from src.database.repositories.activity_event_repository import (
        ActivityEventRepository,
    )
    from src.database.repositories.tp_adjustment_repository import TPAdjustmentRepository
    from src.grid.order_tracker import OrderTracker, TrackedOrder


@dataclass
class PositionTPUpdate:
    """Record of a TP update for a position."""

    order_id: str
    old_tp_percent: float
    new_tp_percent: float
    funding_accumulated: float
    updated_at: datetime


class DynamicTPManager:
    """
    Manages dynamic Take Profit adjustments based on funding rate.

    Periodically checks open positions and adjusts TP to cover:
    - Base TP percentage
    - Accumulated funding costs
    - Safety margin
    """

    # Settlement frequency: 3x per day = every 8 hours
    FUNDING_SETTLEMENT_HOURS = 8

    def __init__(
        self,
        config: DynamicTPConfig,
        client: "BingXClient",
        order_tracker: "OrderTracker",
        symbol: str,
        tp_adjustment_repository: "TPAdjustmentRepository | None" = None,
        account_id: UUID | None = None,
        activity_event_repository: "ActivityEventRepository | None" = None,
    ):
        self.config = config
        self.client = client
        self.order_tracker = order_tracker
        self.symbol = symbol
        self._tp_adjustment_repository = tp_adjustment_repository
        self._account_id = account_id
        self._activity_event_repository = activity_event_repository
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_update: dict[str, datetime] = {}  # order_id -> last update time
        self._update_history: list[PositionTPUpdate] = []

    @property
    def is_enabled(self) -> bool:
        """Check if dynamic TP is enabled."""
        return self.config.enabled

    def _log_activity_event(
        self,
        event_type: str,
        description: str,
        event_data: dict | None = None,
    ) -> None:
        """Log an activity event to the database (non-blocking).

        Creates an activity event record for the dashboard timeline.
        Runs asynchronously to avoid blocking the monitoring loop.

        Args:
            event_type: Type of event (from EventType enum).
            description: Human-readable description of the event.
            event_data: Optional additional event data as dictionary.
        """
        if not self._activity_event_repository or not self._account_id:
            return

        # Persist event directly (sync)
        try:
            self._activity_event_repository.create_event(
                account_id=self._account_id,
                event_type=event_type,
                description=description,
                event_data=event_data,
            )
        except Exception as e:
            orders_logger.warning(f"Failed to log activity event: {e}")

    def start(self) -> None:
        """Start the dynamic TP monitoring task."""
        # Log configuration for debugging
        orders_logger.debug(
            f"Dynamic TP config: enabled={self.config.enabled}, "
            f"base={self.config.base_percent}%, min={self.config.min_percent}%, "
            f"max={self.config.max_percent}%, safety_margin={self.config.safety_margin}%, "
            f"check_interval={self.config.check_interval_minutes}min"
        )

        if not self.config.enabled:
            orders_logger.info("Dynamic TP is disabled (set TP_DYNAMIC_ENABLED=true to enable)")
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        orders_logger.info(
            f"Dynamic TP Manager started (check every {self.config.check_interval_minutes}min)"
        )

    def stop(self) -> None:
        """Stop the dynamic TP monitoring task."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            self._thread = None
        orders_logger.info("Dynamic TP Manager stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_and_update_positions()
            except Exception as e:
                orders_logger.error(f"Error in dynamic TP monitor: {e}")

            # Wait for next check interval
            time.sleep(self.config.check_interval_minutes * 60)

    def _check_and_update_positions(self) -> None:
        """Check all open positions and update TPs if needed."""
        filled_orders = self.order_tracker.filled_orders
        if not filled_orders:
            return

        # Get current funding rate
        try:
            funding_data = self.client.get_funding_rate(self.symbol)
            funding_rate = funding_data["lastFundingRate"]
        except Exception as e:
            orders_logger.error(f"Failed to get funding rate: {e}")
            return

        orders_logger.debug(f"Current funding rate: {funding_rate:.6f} ({funding_rate * 100:.4f}%)")

        for order in filled_orders:
            self._check_position(order, funding_rate)

    def _check_position(self, order: "TrackedOrder", funding_rate: float) -> None:
        """Check a single position and update TP if needed."""
        # Rate limit: don't update same position more than once per 30 min
        last_update = self._last_update.get(order.order_id)
        if last_update:
            minutes_since_update = (datetime.now() - last_update).total_seconds() / 60
            if minutes_since_update < 30:
                return

        # Calculate time position has been open
        if not order.filled_at:
            return

        hours_open = (datetime.now() - order.filled_at).total_seconds() / 3600

        # CRITICAL: Only adjust TP after position has been open for at least 8 hours
        # This ensures the position has experienced at least one funding settlement
        # and prevents premature TP adjustments on newly opened positions
        if hours_open < 8.0:
            orders_logger.debug(
                f"Position {order.order_id[:8]}: {hours_open:.1f}h open, "
                f"skipping TP adjustment (minimum 8h required)"
            )
            return

        # Calculate accumulated funding cost
        # Funding is charged every 8 hours
        funding_settlements = hours_open / self.FUNDING_SETTLEMENT_HOURS
        funding_accumulated = funding_settlements * abs(funding_rate) * 100  # Convert to %

        # Calculate new TP percentage
        new_tp_percent = self._calculate_new_tp(funding_accumulated)

        # Calculate current TP percentage from order
        current_tp_percent = ((order.tp_price - order.entry_price) / order.entry_price) * 100

        # Only update if new TP is significantly higher (> 0.02% difference)
        if new_tp_percent <= current_tp_percent + 0.02:
            return

        # Don't update if price is already close to current TP (within 0.1%)
        try:
            current_price = self.client.get_price(self.symbol)
            distance_to_tp = ((order.tp_price - current_price) / current_price) * 100
            if distance_to_tp < 0.1:
                orders_logger.debug(
                    f"Position {order.order_id[:8]} too close to TP ({distance_to_tp:.2f}%), skipping update"
                )
                return
        except Exception:
            pass  # Continue with update if price check fails

        orders_logger.info(
            f"Position {order.order_id[:8]}: {hours_open:.1f}h open, "
            f"funding accumulated: {funding_accumulated:.4f}%, "
            f"TP: {current_tp_percent:.2f}% -> {new_tp_percent:.2f}%"
        )

        # Calculate new TP price
        new_tp_price = order.entry_price * (1 + new_tp_percent / 100)

        # Update TP on exchange FIRST
        tp_update_success = False
        if not order.exchange_tp_order_id:
            orders_logger.warning(
                f"Position {order.order_id[:8]} has no TP order ID, skipping update"
            )
            return

        try:
            # Get position side dynamically (One-way = "BOTH", Hedge = "LONG"/"SHORT")
            position_side = self.order_tracker.get_position_side()

            # Modify TP order on exchange (cancel old + create new)
            # Grid bot only does LONG positions, so TP side is SELL
            result = self.client.modify_tp_order(
                symbol=self.symbol,
                old_tp_order_id=order.exchange_tp_order_id,
                side="SELL",  # TP for LONG position is SELL
                position_side=position_side,
                quantity=order.quantity,
                new_tp_price=new_tp_price,
            )

            # Update the tracked order with new TP order ID
            order.exchange_tp_order_id = result["newOrderId"]

            orders_logger.info(
                f"TP updated: {order.order_id[:8]} "
                f"TP price: ${order.tp_price:,.2f} -> ${new_tp_price:,.2f} "
                f"(new TP order: {result['newOrderId'][:8]})"
            )
            tp_update_success = True
        except Exception as e:
            orders_logger.error(f"Failed to update TP on exchange for {order.order_id[:8]}: {e}")
            tp_update_success = False

        # ONLY persist if exchange update succeeded
        if tp_update_success:
            # Update in-memory tracking
            old_tp_price = order.tp_price
            order.tp_price = new_tp_price

            # Record the update
            self._last_update[order.order_id] = datetime.now()
            self._update_history.append(
                PositionTPUpdate(
                    order_id=order.order_id,
                    old_tp_percent=current_tp_percent,
                    new_tp_percent=new_tp_percent,
                    funding_accumulated=funding_accumulated,
                    updated_at=datetime.now(),
                )
            )

            # Log TP_ADJUSTED activity event
            self._log_activity_event(
                event_type="TP_ADJUSTED",
                description=(
                    f"Take profit adjusted: {current_tp_percent:.2f}% → {new_tp_percent:.2f}% "
                    f"(funding: {funding_accumulated:.4f}%)"
                ),
                event_data={
                    "order_id": order.order_id,
                    "entry_price": order.entry_price,
                    "old_tp_price": old_tp_price,
                    "new_tp_price": new_tp_price,
                    "old_tp_percent": current_tp_percent,
                    "new_tp_percent": new_tp_percent,
                    "funding_rate": funding_rate,
                    "funding_accumulated": funding_accumulated,
                    "hours_open": hours_open,
                },
            )

            # Persist to database (async, non-blocking)
            if self._tp_adjustment_repository and self._account_id and order.trade_id:
                self._schedule_tp_adjustment_persistence(
                    order=order,
                    old_tp_price=old_tp_price,
                    old_tp_percent=current_tp_percent,
                    new_tp_price=new_tp_price,
                    new_tp_percent=new_tp_percent,
                    funding_rate=funding_rate,
                    funding_accumulated=funding_accumulated,
                    hours_open=hours_open,
                )

            # Update the trade in database with new TP price and order ID
            # This ensures the dashboard shows accurate TP values
            if order.trade_id:
                self._schedule_trade_update(
                    trade_id=order.trade_id,
                    new_tp_price=new_tp_price,
                    new_tp_order_id=order.exchange_tp_order_id,
                )

            # Trim history
            if len(self._update_history) > 100:
                self._update_history.pop(0)

    def _calculate_new_tp(self, funding_accumulated: float) -> float:
        """
        Calculate new TP percentage based on accumulated funding.

        Args:
            funding_accumulated: Accumulated funding cost as percentage

        Returns:
            New TP percentage (clamped between min and max)
        """
        new_tp = self.config.base_percent + funding_accumulated + self.config.safety_margin

        # Clamp to min/max
        new_tp = max(self.config.min_percent, new_tp)
        new_tp = min(self.config.max_percent, new_tp)

        return new_tp

    def get_recommended_tp(self, hours_open: float, funding_rate: float) -> float:
        """
        Get recommended TP for a position based on time open and funding rate.

        This can be used by GridManager to set TP when creating orders.

        Args:
            hours_open: How many hours the position has been open
            funding_rate: Current funding rate (e.g., 0.0001 = 0.01%)

        Returns:
            Recommended TP percentage
        """
        funding_settlements = hours_open / self.FUNDING_SETTLEMENT_HOURS
        funding_accumulated = funding_settlements * abs(funding_rate) * 100

        return self._calculate_new_tp(funding_accumulated)

    def get_positions_needing_update(self) -> list[str]:
        """Get list of order IDs that need TP update."""
        return [update.order_id for update in self._update_history[-10:]]

    def get_stats(self) -> dict:
        """Get statistics about TP updates."""
        return {
            "enabled": self.config.enabled,
            "running": self._running,
            "total_updates": len(self._update_history),
            "recent_updates": [
                {
                    "order_id": u.order_id[:8],
                    "old_tp": f"{u.old_tp_percent:.2f}%",
                    "new_tp": f"{u.new_tp_percent:.2f}%",
                    "funding": f"{u.funding_accumulated:.4f}%",
                    "time": u.updated_at.isoformat(),
                }
                for u in self._update_history[-5:]
            ],
        }

    def _schedule_tp_adjustment_persistence(
        self,
        order: "TrackedOrder",
        old_tp_price: float,
        old_tp_percent: float,
        new_tp_price: float,
        new_tp_percent: float,
        funding_rate: float,
        funding_accumulated: float,
        hours_open: float,
    ) -> None:
        """Schedule TP adjustment persistence to database (non-blocking).

        NOTE: This should ONLY be called after exchange TP update succeeds.

        Args:
            order: The tracked order being adjusted
            old_tp_price: Previous take profit price
            old_tp_percent: Previous take profit percentage
            new_tp_price: New take profit price
            new_tp_percent: New take profit percentage
            funding_rate: Current funding rate
            funding_accumulated: Accumulated funding cost as percentage
            hours_open: Hours the position has been open
        """
        from decimal import Decimal

        # Persist adjustment directly (sync)
        if not self._tp_adjustment_repository or not order.trade_id:
            return

        try:
            self._tp_adjustment_repository.save_adjustment(
                trade_id=order.trade_id,
                old_tp_price=Decimal(str(old_tp_price)),
                new_tp_price=Decimal(str(new_tp_price)),
                old_tp_percent=Decimal(str(old_tp_percent)),
                new_tp_percent=Decimal(str(new_tp_percent)),
                funding_rate=Decimal(str(funding_rate)),
                funding_accumulated=Decimal(str(funding_accumulated)),
                hours_open=Decimal(str(hours_open)),
            )
            orders_logger.info(f"TP adjustment persisted: {order.order_id[:8]}")
        except Exception as e:
            orders_logger.warning(
                f"Failed to persist TP adjustment: {e}. Adjustment kept in memory only."
            )

    def _schedule_trade_update(
        self,
        trade_id: UUID,
        new_tp_price: float,
        new_tp_order_id: str | None,
    ) -> None:
        """Schedule trade update in database (non-blocking).

        Updates the trade record with new TP price and exchange_tp_order_id.
        This ensures the dashboard shows accurate TP values.

        Args:
            trade_id: UUID of the trade to update
            new_tp_price: New take profit price
            new_tp_order_id: New exchange TP order ID
        """
        from decimal import Decimal

        from src.database.engine import get_session
        from src.database.repositories.trade_repository import TradeRepository

        # Persist trade update directly (sync)
        try:
            with get_session() as session:
                trade_repo = TradeRepository(session)

                # Update tp_price and exchange_tp_order_id
                trade_repo.update_tp(
                    trade_id=trade_id,
                    new_tp_price=Decimal(str(new_tp_price)),
                    new_tp_order_id=new_tp_order_id,
                )

                orders_logger.debug(
                    f"Trade {str(trade_id)[:8]} updated with new TP: ${new_tp_price:,.2f}, "
                    f"TP order: {new_tp_order_id[:8] if new_tp_order_id else 'None'}"
                )
        except Exception as e:
            orders_logger.error(f"Failed to update trade {str(trade_id)[:8]} in database: {e}")
