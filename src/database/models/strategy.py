"""Strategy model for unified trading configuration."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .account import Account
    from .ema_filter_config import EMAFilterConfig
    from .macd_filter_config import MACDFilterConfig


class Strategy(Base):
    """Unified trading strategy configuration model.

    Aggregates all trading configuration (trading, grid, dynamic TP) into a single
    entity per account. Replaces separate TradingConfig and GridConfig models.

    Attributes:
        id: Unique strategy identifier (UUID).
        account_id: Foreign key to accounts table.
        name: Human-readable strategy name.
        is_active: Whether this strategy is currently active.
        symbol: Trading pair (e.g., 'BTC-USDT').

        leverage: Leverage multiplier (1-125x).
        order_size_usdt: Order size in USDT per grid level.
        margin_mode: Margin mode ('crossed' or 'isolated').

        take_profit_percent: Base take profit percentage.
        tp_dynamic_enabled: Enable dynamic TP based on funding rate.
        tp_dynamic_base: Base TP percentage for dynamic calculation.
        tp_dynamic_min: Minimum TP percentage (floor).
        tp_dynamic_max: Maximum TP percentage (ceiling).
        tp_dynamic_safety_margin: Safety margin above funding cost.
        tp_dynamic_check_interval: Check interval in minutes.

        spacing_type: Grid spacing type ('fixed' or 'percentage').
        spacing_value: Grid spacing value (USD or percentage).
        range_percent: Grid range as percentage from current price.
        max_total_orders: Maximum total orders (pending + filled).
        anchor_mode: Grid anchor mode ('none', 'hundred', 'thousand').
        anchor_threshold: Anchor threshold value in USD.

        created_at: Timestamp of strategy creation.
        updated_at: Timestamp of last update.

    Constraints:
        - Only one active strategy per account (partial unique index).
        - account_id references accounts(id) with CASCADE delete.
    """

    __tablename__ = "strategies"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Core fields
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, default="BTC-USDT")

    # Risk parameters
    leverage: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    order_size_usdt: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, default=Decimal("100.00")
    )
    margin_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="crossed")

    # Take profit parameters
    take_profit_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.50")
    )

    # Dynamic TP parameters
    tp_dynamic_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tp_dynamic_base: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.30")
    )
    tp_dynamic_min: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.30")
    )
    tp_dynamic_max: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("1.00")
    )
    tp_dynamic_safety_margin: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.05")
    )
    tp_dynamic_check_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # Grid parameters
    spacing_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    spacing_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("100.0")
    )
    range_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4), nullable=False, default=Decimal("5.0")
    )
    max_total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    anchor_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    anchor_threshold: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("100.0")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="strategies")
    ema_filter_config: Mapped["EMAFilterConfig | None"] = relationship(
        "EMAFilterConfig", back_populates="strategy", uselist=False, cascade="all, delete-orphan"
    )
    macd_filter_config: Mapped["MACDFilterConfig | None"] = relationship(
        "MACDFilterConfig", back_populates="strategy", uselist=False, cascade="all, delete-orphan"
    )

    # Constraints: Only one active strategy per account
    __table_args__ = (
        Index(
            "ix_strategies_account_active",
            "account_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    def __repr__(self) -> str:
        """String representation of Strategy."""
        return (
            f"<Strategy(id={self.id}, name={self.name!r}, "
            f"account_id={self.account_id}, is_active={self.is_active}, "
            f"symbol={self.symbol}, leverage={self.leverage}x)>"
        )
