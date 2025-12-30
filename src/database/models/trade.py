"""Trade model for storing executed trades and their results."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class Trade(Base):
    """Trade model for storing executed trades.

    Stores information about completed trades including entry/exit prices,
    profit/loss calculations, and grid level information.

    Attributes:
        id: Unique trade identifier (UUID).
        user_id: ID of the user who owns this trade.
        account_type: Type of account (demo or live).
        symbol: Trading pair symbol.
        side: Trade direction (LONG or SHORT).
        entry_price: Price at which the position was opened.
        exit_price: Price at which the position was closed.
        quantity: Amount traded.
        pnl: Profit and loss in absolute value.
        pnl_percent: Profit and loss as percentage.
        grid_level: Grid level at which the trade was executed (optional).
        entry_at: Timestamp when position was opened.
        closed_at: Timestamp when position was closed.
        created_at: Timestamp of record creation.
    """

    __tablename__ = "trades"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # User and account info
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(10), nullable=False, default="demo")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, default="BTC-USDT")
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")

    # Trade execution data
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    # Profit/Loss calculations
    pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    pnl_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Grid information
    grid_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    entry_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC))

    # Composite indexes for efficient queries
    __table_args__ = (
        Index("idx_trades_user_closed", "user_id", "closed_at"),
        Index("idx_trades_user_account", "user_id", "account_type"),
    )

    def __repr__(self) -> str:
        """String representation of Trade."""
        return (
            f"<Trade(id={self.id}, user_id={self.user_id}, "
            f"symbol={self.symbol}, pnl={self.pnl}, closed_at={self.closed_at})>"
        )
