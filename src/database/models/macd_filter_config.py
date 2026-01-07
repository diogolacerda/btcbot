"""MACDFilterConfig model for MACD filter configuration per strategy."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .strategy import Strategy


class MACDFilterConfig(Base):
    """MACD filter configuration model linked to a Strategy.

    Stores MACD indicator parameters for filtering trading signals. Each Strategy
    can have exactly one MACDFilterConfig (one-to-one relationship).

    Attributes:
        id: Unique configuration identifier (UUID).
        strategy_id: Foreign key to strategies table.
        enabled: Whether the MACD filter is enabled.
        fast_period: Fast EMA period for MACD calculation.
        slow_period: Slow EMA period for MACD calculation.
        signal_period: Signal line EMA period.
        timeframe: Candle timeframe for MACD calculation (e.g., '1h', '4h').
        created_at: Timestamp of configuration creation.
        updated_at: Timestamp of last update.

    Constraints:
        - strategy_id is unique (one-to-one with Strategy).
        - strategy_id references strategies(id) with CASCADE delete.
    """

    __tablename__ = "macd_filter_configs"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to strategies
    strategy_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # MACD filter parameters
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fast_period: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    slow_period: Mapped[int] = mapped_column(Integer, nullable=False, default=26)
    signal_period: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="1h")

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
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="macd_filter_config")

    # Constraints: one-to-one with Strategy
    __table_args__ = (UniqueConstraint("strategy_id", name="uq_macd_filter_configs_strategy_id"),)

    def __repr__(self) -> str:
        """String representation of MACDFilterConfig."""
        return (
            f"<MACDFilterConfig(id={self.id}, strategy_id={self.strategy_id}, "
            f"enabled={self.enabled}, fast={self.fast_period}, slow={self.slow_period}, "
            f"signal={self.signal_period}, timeframe={self.timeframe!r})>"
        )
