"""BotState model for persisting MACD cycle state across restarts."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .account import Account


class BotState(Base):
    """BotState model for managing bot cycle state persistence.

    Stores the current state of the MACD cycle to enable recovery after
    bot restart or crash. Each account has a single state record.

    Attributes:
        id: Unique bot state identifier (UUID).
        account_id: Foreign key to accounts table (one-to-one relationship).
        cycle_activated: Whether the MACD cycle has been activated.
        last_state: Last known GridState (WAIT, ACTIVATE, ACTIVE, PAUSE, INACTIVE).
        is_manual_override: Whether the activation was manual (True) or automatic (False).
            Manual activations are restored more aggressively on restart.
        activated_at: Timestamp when cycle was first activated.
        last_state_change_at: Timestamp of last state change.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "bot_state"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts (one-to-one)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One state per account
        index=True,
    )

    # MACD cycle state
    cycle_activated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_state: Mapped[str] = mapped_column(String(20), nullable=False, default="WAIT")
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps for state tracking
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_state_change_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    account: Mapped["Account"] = relationship("Account", back_populates="bot_state")

    # Constraints (enforce one state per account at DB level)
    __table_args__ = (UniqueConstraint("account_id", name="uq_bot_state_account"),)

    def __repr__(self) -> str:
        """String representation of BotState."""
        status = "activated" if self.cycle_activated else "not activated"
        return f"<BotState(id={self.id}, account_id={self.account_id}, state={self.last_state}, {status})>"
