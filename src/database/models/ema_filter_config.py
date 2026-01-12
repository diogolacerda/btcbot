"""EMAFilterConfig model for EMA filter configuration per strategy."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .strategy import Strategy


class EMAFilterConfig(Base):
    """EMA filter configuration model linked to a Strategy.

    Stores EMA indicator parameters for filtering trading signals. Each Strategy
    can have exactly one EMAFilterConfig (one-to-one relationship).

    The EMA filter is part of the Impulse System (Alexander Elder) and works
    alongside MACD to determine trade direction:
    - Rising EMA: Allows long trades (bullish trend)
    - Falling EMA: Protects existing orders (bearish trend)

    Attributes:
        id: Unique configuration identifier (UUID).
        strategy_id: Foreign key to strategies table.
        enabled: Whether the EMA filter is enabled.
        period: EMA period for calculation (default 13).
        timeframe: Candle timeframe for EMA calculation (e.g., '1h', '4h').
        allow_on_rising: Allow new orders when EMA is rising (default True).
        allow_on_falling: Allow new orders when EMA is falling (default False).
        created_at: Timestamp of configuration creation.
        updated_at: Timestamp of last update.

    Constraints:
        - strategy_id is unique (one-to-one with Strategy).
        - strategy_id references strategies(id) with CASCADE delete.
    """

    __tablename__ = "ema_filter_configs"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to strategies
    strategy_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # EMA filter parameters
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    period: Mapped[int] = mapped_column(Integer, nullable=False, default=13)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="1h")
    allow_on_rising: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_on_falling: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="ema_filter_config")

    # Constraints: one-to-one with Strategy
    __table_args__ = (UniqueConstraint("strategy_id", name="uq_ema_filter_configs_strategy_id"),)

    def __repr__(self) -> str:
        """String representation of EMAFilterConfig."""
        return (
            f"<EMAFilterConfig(id={self.id}, strategy_id={self.strategy_id}, "
            f"enabled={self.enabled}, period={self.period}, timeframe={self.timeframe!r}, "
            f"allow_on_rising={self.allow_on_rising}, allow_on_falling={self.allow_on_falling})>"
        )
