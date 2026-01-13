"""Trade reconciliation module for syncing database state with BingX exchange.

This module provides periodic reconciliation to detect and fix drift between:
- Database trades (source of truth for historical data)
- BingX exchange state (source of truth for current positions)

Reconciliation fixes:
1. Missing TP order IDs in database (BUG #1)
2. Trades not closed when TP executed (BUG #2)

Note: Orphaned TPs on BingX without database records are logged as warnings
but not automatically corrected to avoid creating artificial trade data.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.client.bingx_client import BingXClient
from src.database.engine import get_session
from src.database.repositories.trade_repository import TradeRepository
from src.utils.logger import main_logger as logger


class TradeReconciliation:
    """Reconciles database trades with BingX exchange state."""

    def __init__(self, client: BingXClient, account_id: UUID, symbol: str = "BTC-USDT"):
        """Initialize reconciliation service.

        Args:
            client: BingX API client
            account_id: Account UUID for trade filtering
            symbol: Trading symbol (default: BTC-USDT)
        """
        self.client = client
        self.account_id = account_id
        self.symbol = symbol

    def reconcile(self) -> dict:
        """Run full reconciliation between database and BingX.

        Returns:
            dict: Reconciliation statistics
                - tp_ids_fixed: Number of NULL TP order IDs fixed
                - trades_closed: Number of orphaned trades closed
        """
        stats = {
            "tp_ids_fixed": 0,
            "trades_closed": 0,
        }

        try:
            # Get BingX state
            open_orders = self.client.get_open_orders(self.symbol)
            tp_orders = {
                str(o.get("orderId")): o
                for o in open_orders
                if o.get("type") in ["TAKE_PROFIT_MARKET", "TAKE_PROFIT"]
            }

            # Get database state
            with get_session() as session:
                repo = TradeRepository(session)
                db_trades = repo.get_open_trades(self.account_id)

                # Fix 1: Update missing TP order IDs
                stats["tp_ids_fixed"] = self._fix_missing_tp_ids(repo, db_trades, tp_orders)

                # Fix 2: Close trades where TP was executed
                stats["trades_closed"] = self._close_executed_trades(repo, db_trades, tp_orders)

            if any(stats.values()):
                logger.info(
                    f"Reconciliation completed: {stats['tp_ids_fixed']} TP IDs fixed, "
                    f"{stats['trades_closed']} trades closed"
                )

        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")

        return stats

    def _fix_missing_tp_ids(self, repo: TradeRepository, db_trades: list, tp_orders: dict) -> int:
        """Fix trades with NULL exchange_tp_order_id by matching with BingX TPs.

        Args:
            repo: Trade repository
            db_trades: List of open trades from database
            tp_orders: Dict of TP orders from BingX {order_id: order_data}

        Returns:
            int: Number of TP IDs fixed
        """
        fixed_count = 0

        for trade in db_trades:
            if trade.exchange_tp_order_id:
                continue  # Already has TP order ID

            # Try to match TP by price and quantity
            matching_tp = self._find_matching_tp(trade, list(tp_orders.values()))

            if matching_tp:
                tp_order_id = str(matching_tp.get("orderId"))
                repo.update_tp(
                    trade_id=trade.id,
                    new_tp_price=trade.tp_price,
                    new_tp_order_id=tp_order_id,
                )
                fixed_count += 1
                logger.info(
                    f"Fixed missing TP order ID for trade {str(trade.id)[:8]}: {tp_order_id}"
                )

        return fixed_count

    def _close_executed_trades(
        self, repo: TradeRepository, db_trades: list, tp_orders: dict
    ) -> int:
        """Close trades where TP order no longer exists on BingX (was executed).

        Args:
            repo: Trade repository
            db_trades: List of open trades from database
            tp_orders: Dict of TP orders from BingX {order_id: order_data}

        Returns:
            int: Number of trades closed
        """
        closed_count = 0

        for trade in db_trades:
            if not trade.exchange_tp_order_id:
                continue  # Can't verify without TP order ID

            # Check if TP order still exists on BingX
            if trade.exchange_tp_order_id not in tp_orders:
                # TP order doesn't exist = was executed
                exit_price = trade.tp_price
                pnl = (exit_price - trade.entry_price) * trade.quantity * Decimal("10")
                pnl -= trade.trading_fee + trade.funding_fee
                pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100

                repo.update_trade_exit(
                    trade_id=trade.id,
                    exit_price=exit_price,
                    pnl=pnl,
                    pnl_percent=pnl_percent,
                    closed_at=datetime.now(UTC),
                    status="CLOSED",
                )
                closed_count += 1
                logger.info(
                    f"Closed executed trade {str(trade.id)[:8]}: "
                    f"${float(trade.entry_price):,.2f} → ${float(exit_price):,.2f} "
                    f"(PnL: ${float(pnl):,.2f})"
                )

        return closed_count

    def _find_matching_tp(
        self, trade: Any, tp_orders: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Find TP order that matches trade by price and quantity.

        Args:
            trade: Trade object from database
            tp_orders: List of TP orders from BingX

        Returns:
            dict: Matching TP order or None
        """
        for tp_order in tp_orders:
            tp_price = float(tp_order.get("stopPrice", 0))
            tp_quantity = float(tp_order.get("origQty", 0))

            # Match with tolerance (±0.01 for price, ±0.00001 for quantity)
            price_match = abs(tp_price - float(trade.tp_price)) < 0.01
            quantity_match = abs(tp_quantity - float(trade.quantity)) < 0.00001

            if price_match and quantity_match:
                return tp_order

        return None
