"""TP Adjustment model for tracking Take Profit adjustments made by Dynamic TP."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class TPAdjustment(Base):
    """TP Adjustment model for tracking Take Profit adjustments.

    Stores historical records of all Take Profit adjustments made by the Dynamic TP
    Manager (BE-007) based on funding rate. This enables:
    - Audit trail of all TP adjustments
    - Analytics on funding rate impact on trades
    - Debug and troubleshooting of Dynamic TP behavior

    Attributes:
        id: Unique adjustment identifier (UUID).
        trade_id: FK reference to trades table.
        old_tp_price: Take-profit price before adjustment.
        new_tp_price: Take-profit price after adjustment.
        old_tp_percent: Take-profit percentage before adjustment.
        new_tp_percent: Take-profit percentage after adjustment.
        funding_rate: Current funding rate at time of adjustment.
        funding_accumulated: Accumulated funding cost as percentage.
        hours_open: Hours the position has been open.
        adjusted_at: Timestamp when adjustment was made.
    """

    __tablename__ = "tp_adjustments"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to trades
    trade_id: Mapped[UUID] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Values before/after adjustment
    old_tp_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    new_tp_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    old_tp_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    new_tp_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Reason for adjustment
    funding_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    funding_accumulated: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    hours_open: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Timestamp
    adjusted_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_tp_adjustments_trade_id", "trade_id"),
        Index("idx_tp_adjustments_adjusted_at", "adjusted_at"),
    )

    def __repr__(self) -> str:
        """String representation of TPAdjustment."""
        return (
            f"<TPAdjustment(id={self.id}, trade_id={self.trade_id}, "
            f"old_tp_percent={self.old_tp_percent}, new_tp_percent={self.new_tp_percent})>"
        )
