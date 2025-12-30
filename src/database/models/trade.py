"""Trade model for storing executed trades and their results."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class Trade(Base):
    """Trade model for storing executed trades.

    Stores information about both open and closed trades, allowing state recovery
    after restart and historical analytics.

    Attributes:
        id: Unique trade identifier (UUID).
        account_id: FK reference to accounts table.
        exchange_order_id: Order ID from the exchange (for traceability).
        exchange_tp_order_id: Take-profit order ID from the exchange.
        symbol: Trading pair symbol.
        side: Trade direction (LONG or SHORT).
        leverage: Leverage used for this trade.
        entry_price: Price at which the position was opened.
        exit_price: Price at which the position was closed (nullable for open trades).
        quantity: Amount traded.
        tp_price: Take-profit target price (updatable by Dynamic TP).
        tp_percent: Take-profit target percentage.
        pnl: Profit and loss in absolute value (nullable for open trades).
        pnl_percent: Profit and loss as percentage (nullable for open trades).
        trading_fee: Trading fees incurred.
        funding_fee: Funding fees incurred.
        status: Trade status (OPEN, CLOSED, CANCELLED).
        grid_level: Grid level at which the trade was executed (optional).
        opened_at: Timestamp when position was opened.
        filled_at: Timestamp when order was filled.
        closed_at: Timestamp when position was closed.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "trades"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts
    # NOTE: FK constraint will be added when accounts table is created (DB-013)
    # For now, just storing account_id as UUID
    account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # Exchange data for traceability
    exchange_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exchange_tp_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Trade configuration
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, default="BTC-USDT")
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")
    leverage: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Trade execution data
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    # Take Profit (updatable by Dynamic TP Manager)
    tp_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    tp_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    # Profit/Loss calculations
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    pnl_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    # Fees
    trading_fee: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
    funding_fee: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")

    # Grid information (optional, useful for grid bot strategy)
    grid_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    filled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(UTC),
    )

    # Composite indexes for efficient queries
    __table_args__ = (
        Index("idx_trades_account_id", "account_id"),
        Index("idx_trades_status", "status"),
        Index("idx_trades_account_status", "account_id", "status"),
        Index("idx_trades_account_closed", "account_id", "closed_at"),
        Index(
            "idx_trades_exchange_order",
            "account_id",
            "exchange_order_id",
            unique=True,
            postgresql_where=text("exchange_order_id IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        """String representation of Trade."""
        return (
            f"<Trade(id={self.id}, account_id={self.account_id}, "
            f"symbol={self.symbol}, status={self.status}, pnl={self.pnl})>"
        )
