"""Trade repository for managing trade records."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.trade import Trade
from src.database.repositories.base_repository import BaseRepository
from src.utils.logger import main_logger


class TradeRepository(BaseRepository[Trade]):
    """Repository for Trade CRUD operations.

    Inherits from BaseRepository to leverage common CRUD operations
    while providing trade-specific methods.

    Provides async methods for creating, reading, and updating trade records
    for historical analytics and state recovery.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, Trade)

    async def save_trade(self, trade_data: dict) -> UUID:
        """Save a new trade record.

        Uses BaseRepository.create() internally for database operations.
        If a trade with the same exchange_order_id already exists, returns
        the existing trade ID (idempotent operation).

        Args:
            trade_data: Dictionary containing trade data with keys:
                - account_id (UUID): Account identifier
                - exchange_order_id (str, optional): Exchange order ID
                - exchange_tp_order_id (str, optional): Exchange TP order ID
                - symbol (str): Trading symbol
                - side (str): Trade direction (LONG/SHORT)
                - leverage (int): Leverage used
                - entry_price (Decimal): Entry price
                - quantity (Decimal): Trade quantity
                - tp_price (Decimal, optional): Take profit price
                - tp_percent (Decimal, optional): Take profit percentage
                - trading_fee (Decimal, optional): Trading fee
                - funding_fee (Decimal, optional): Funding fee
                - status (str, optional): Trade status (default: OPEN)
                - grid_level (int, optional): Grid level
                - opened_at (datetime, optional): Opening timestamp
                - filled_at (datetime, optional): Fill timestamp

        Returns:
            UUID of the created or existing trade.

        Raises:
            Exception: If database operation fails.
        """
        try:
            # Check if trade already exists (race condition protection)
            exchange_order_id = trade_data.get("exchange_order_id")
            if exchange_order_id:
                existing_trade = await self.get_by_exchange_order_id(
                    account_id=trade_data["account_id"],
                    exchange_order_id=exchange_order_id,
                )
                if existing_trade:
                    main_logger.debug(
                        f"Trade with exchange_order_id {exchange_order_id} already exists, "
                        f"returning existing ID: {existing_trade.id}"
                    )
                    return existing_trade.id  # type: ignore[no-any-return]

            trade = Trade(
                account_id=trade_data["account_id"],
                exchange_order_id=exchange_order_id,
                exchange_tp_order_id=trade_data.get("exchange_tp_order_id"),
                symbol=trade_data.get("symbol", "BTC-USDT"),
                side=trade_data.get("side", "LONG"),
                leverage=trade_data.get("leverage", 10),
                entry_price=trade_data["entry_price"],
                exit_price=trade_data.get("exit_price"),
                quantity=trade_data["quantity"],
                tp_price=trade_data.get("tp_price"),
                tp_percent=trade_data.get("tp_percent"),
                pnl=trade_data.get("pnl"),
                pnl_percent=trade_data.get("pnl_percent"),
                trading_fee=trade_data.get("trading_fee", Decimal("0")),
                funding_fee=trade_data.get("funding_fee", Decimal("0")),
                status=trade_data.get("status", "OPEN"),
                grid_level=trade_data.get("grid_level"),
                opened_at=trade_data.get("opened_at"),
                filled_at=trade_data.get("filled_at"),
                closed_at=trade_data.get("closed_at"),
            )
            # Use inherited create method
            created_trade = await super().create(trade)
            main_logger.info(
                f"Trade saved: {created_trade.id} for account {created_trade.account_id}"
            )
            return created_trade.id  # type: ignore[no-any-return]
        except Exception as e:
            main_logger.error(f"Error saving trade: {e}")
            raise

    async def get_trades_by_account(
        self,
        account_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Trade]:
        """Get trades for an account with pagination.

        Args:
            account_id: Account UUID.
            limit: Maximum number of trades to return.
            offset: Number of trades to skip.

        Returns:
            List of Trade instances ordered by created_at DESC.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = (
                select(Trade)
                .where(Trade.account_id == account_id)
                .order_by(Trade.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            main_logger.error(f"Error fetching trades for account {account_id}: {e}")
            raise

    async def get_trades_by_period(
        self,
        account_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[Trade]:
        """Get trades for an account within a time period.

        Args:
            account_id: Account UUID.
            start: Start datetime (inclusive).
            end: End datetime (inclusive).

        Returns:
            List of Trade instances in the specified period.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = (
                select(Trade)
                .where(
                    Trade.account_id == account_id,
                    Trade.opened_at >= start,
                    Trade.opened_at <= end,
                )
                .order_by(Trade.opened_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            main_logger.error(
                f"Error fetching trades for account {account_id} in period {start} - {end}: {e}"
            )
            raise

    async def get_open_trades(self, account_id: UUID) -> list[Trade]:
        """Get all open trades for an account.

        Args:
            account_id: Account UUID.

        Returns:
            List of Trade instances with status='OPEN'.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = (
                select(Trade)
                .where(
                    Trade.account_id == account_id,
                    Trade.status == "OPEN",
                )
                .order_by(Trade.opened_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            main_logger.error(f"Error fetching open trades for account {account_id}: {e}")
            raise

    async def update_trade_exit(
        self,
        trade_id: UUID,
        exit_price: Decimal,
        pnl: Decimal,
        *,
        pnl_percent: Decimal | None = None,
        closed_at: datetime | None = None,
        status: str = "CLOSED",
    ) -> None:
        """Update trade exit information when position is closed.

        Uses BaseRepository.get_by_id() and update() internally.

        Args:
            trade_id: Trade UUID.
            exit_price: Exit price.
            pnl: Profit and loss in absolute value.
            pnl_percent: Profit and loss percentage (optional).
            closed_at: Close timestamp (defaults to now if not provided).
            status: Trade status (default: CLOSED).

        Raises:
            ValueError: If trade is not found.
            Exception: If database operation fails.
        """
        try:
            # Use inherited get_by_id method
            trade = await super().get_by_id(trade_id)

            if not trade:
                raise ValueError(f"Trade {trade_id} not found")

            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_percent = pnl_percent
            trade.closed_at = closed_at if closed_at is not None else datetime.now(UTC)
            trade.status = status

            # Use inherited update method
            await super().update(trade)
            main_logger.info(f"Trade {trade_id} updated with exit data: pnl={pnl}")
        except ValueError:
            raise
        except Exception as e:
            main_logger.error(f"Error updating trade exit for {trade_id}: {e}")
            raise

    async def get_by_exchange_order_id(
        self,
        account_id: UUID,
        exchange_order_id: str,
    ) -> Trade | None:
        """Get trade by exchange order ID.

        Args:
            account_id: Account UUID.
            exchange_order_id: Exchange order ID.

        Returns:
            Trade instance or None if not found.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = select(Trade).where(
                Trade.account_id == account_id,
                Trade.exchange_order_id == exchange_order_id,
            )
            result = await self.session.execute(stmt)
            trade: Trade | None = result.scalar_one_or_none()
            return trade
        except Exception as e:
            main_logger.error(f"Error fetching trade by exchange order {exchange_order_id}: {e}")
            raise
