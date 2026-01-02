"""Trading configuration model for dynamic bot configuration."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .account import Account


class TradingConfig(Base):
    """Trading configuration model for managing bot trading parameters.

    Stores trading configuration per account, allowing dynamic updates
    without restarting the bot.

    Attributes:
        id: Unique configuration identifier (UUID).
        account_id: Foreign key to accounts table (one config per account).
        symbol: Trading pair (e.g., 'BTC-USDT').
        leverage: Leverage multiplier (1-125x).
        order_size_usdt: Order size in USDT.
        margin_mode: Margin mode ('CROSSED' or 'ISOLATED').
        take_profit_percent: Take profit percentage (0.1 - 5.0).
        tp_dynamic_enabled: Enable dynamic TP based on funding rate.
        tp_base_percent: Base TP percentage for dynamic TP.
        tp_min_percent: Minimum TP percentage (never below this).
        tp_max_percent: Maximum TP percentage (cap).
        tp_safety_margin: Safety margin above funding cost.
        tp_check_interval_min: How often to check positions (minutes).
        created_at: Timestamp of configuration creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "trading_configs"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Trading parameters
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, default="BTC-USDT")
    leverage: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    order_size_usdt: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, default=Decimal("100.00")
    )
    margin_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="CROSSED")
    take_profit_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.50")
    )

    # Dynamic TP parameters (BE-035)
    tp_dynamic_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tp_base_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.30")
    )
    tp_min_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.30")
    )
    tp_max_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("1.00")
    )
    tp_safety_margin: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0.05")
    )
    tp_check_interval_min: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

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
    account: Mapped["Account"] = relationship("Account", back_populates="trading_config")

    # Constraints
    __table_args__ = (UniqueConstraint("account_id", name="uq_trading_config_account"),)

    def __repr__(self) -> str:
        """String representation of TradingConfig."""
        return (
            f"<TradingConfig(id={self.id}, account_id={self.account_id}, "
            f"symbol={self.symbol}, leverage={self.leverage}x, "
            f"order_size={self.order_size_usdt} USDT, tp={self.take_profit_percent}%)>"
        )
