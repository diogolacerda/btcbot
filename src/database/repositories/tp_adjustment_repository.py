"""Repository for TPAdjustment persistence."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.tp_adjustment import TPAdjustment
from src.database.repositories.base_repository import BaseRepository


class TPAdjustmentRepository(BaseRepository[TPAdjustment]):
    """Repository for TPAdjustment persistence.

    Provides methods for persisting and querying TP adjustment records created
    by the Dynamic TP Manager (BE-007). Inherits standard CRUD operations from
    BaseRepository.

    Example:
        async with get_session() as session:
            repo = TPAdjustmentRepository(session)

            # Save new adjustment
            adjustment = await repo.save_adjustment(
                trade_id=trade.id,
                old_tp_price=Decimal("50000"),
                new_tp_price=Decimal("50500"),
                old_tp_percent=Decimal("0.5"),
                new_tp_percent=Decimal("0.6"),
                funding_rate=Decimal("0.0001"),
                funding_accumulated=Decimal("0.1"),
                hours_open=Decimal("8.5"),
            )

            # Get adjustment history for a trade
            adjustments = await repo.get_by_trade(trade.id)
    """

    def __init__(self, session: AsyncSession):
        """Initialize TPAdjustmentRepository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, TPAdjustment)

    async def save_adjustment(
        self,
        trade_id: UUID,
        old_tp_price: Decimal,
        new_tp_price: Decimal,
        old_tp_percent: Decimal,
        new_tp_percent: Decimal,
        funding_rate: Decimal | None = None,
        funding_accumulated: Decimal | None = None,
        hours_open: Decimal | None = None,
    ) -> TPAdjustment:
        """Save a TP adjustment record.

        Helper method to create and persist a TPAdjustment record with all
        necessary parameters. This is the primary method used by the Dynamic TP
        Manager to record adjustments.

        Args:
            trade_id: UUID of the trade being adjusted.
            old_tp_price: Take-profit price before adjustment.
            new_tp_price: Take-profit price after adjustment.
            old_tp_percent: Take-profit percentage before adjustment.
            new_tp_percent: Take-profit percentage after adjustment.
            funding_rate: Current funding rate (optional).
            funding_accumulated: Accumulated funding cost as percentage (optional).
            hours_open: Hours the position has been open (optional).

        Returns:
            Created TPAdjustment instance with database-generated ID.

        Raises:
            Exception: If database operation fails.

        Example:
            adjustment = await repo.save_adjustment(
                trade_id=uuid4(),
                old_tp_price=Decimal("50000"),
                new_tp_price=Decimal("50500"),
                old_tp_percent=Decimal("0.5"),
                new_tp_percent=Decimal("0.6"),
                funding_rate=Decimal("0.0001"),
            )
        """
        adjustment = TPAdjustment(
            trade_id=trade_id,
            old_tp_price=old_tp_price,
            new_tp_price=new_tp_price,
            old_tp_percent=old_tp_percent,
            new_tp_percent=new_tp_percent,
            funding_rate=funding_rate,
            funding_accumulated=funding_accumulated,
            hours_open=hours_open,
        )
        return await super().create(adjustment)

    async def get_by_trade(self, trade_id: UUID) -> list[TPAdjustment]:
        """Get all adjustments for a trade.

        Retrieves complete adjustment history for a specific trade, ordered
        by most recent first. Useful for analytics and debugging.

        Args:
            trade_id: UUID of the trade to retrieve adjustments for.

        Returns:
            List of TPAdjustment instances for the trade, ordered by adjusted_at desc.
            Empty list if no adjustments found.

        Raises:
            Exception: If database operation fails.

        Example:
            adjustments = await repo.get_by_trade(trade_id)
            for adj in adjustments:
                print(f"Adjusted from {adj.old_tp_percent}% to {adj.new_tp_percent}%")
        """
        try:
            result = await self.session.execute(
                select(TPAdjustment)
                .where(TPAdjustment.trade_id == trade_id)
                .order_by(TPAdjustment.adjusted_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Error fetching adjustments for trade {trade_id}: {e}") from e

    async def get_recent(
        self,
        limit: int = 100,
        start_date: datetime | None = None,
    ) -> list[TPAdjustment]:
        """Get recent adjustments with optional date filter.

        Retrieves recent TP adjustments across all trades, useful for monitoring
        Dynamic TP behavior and analytics on funding rate impact.

        Args:
            limit: Maximum number of adjustments to return. Defaults to 100.
            start_date: Optional datetime filter - only return adjustments after this date.

        Returns:
            List of TPAdjustment instances, ordered by adjusted_at desc.
            Empty list if no adjustments found.

        Raises:
            Exception: If database operation fails.

        Example:
            # Get last 50 adjustments
            recent = await repo.get_recent(limit=50)

            # Get adjustments from last 24 hours
            from datetime import datetime, timedelta, UTC
            yesterday = datetime.now(UTC) - timedelta(days=1)
            recent = await repo.get_recent(start_date=yesterday)
        """
        try:
            query = select(TPAdjustment).order_by(TPAdjustment.adjusted_at.desc())

            if start_date:
                query = query.where(TPAdjustment.adjusted_at >= start_date)

            result = await self.session.execute(query.limit(limit))
            return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Error fetching recent adjustments: {e}") from e
