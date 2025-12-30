"""Account model for multi-exchange and multi-mode trading accounts."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from .bot_state import BotState
    from .user import User


class Account(Base):
    """Account model for managing trading accounts across exchanges.

    Supports multiple accounts per user, multiple exchanges, and both demo/live modes.
    The same API key used in demo and live modes will have 2 separate account records.

    Attributes:
        id: Unique account identifier (UUID).
        user_id: Foreign key to users table.
        exchange: Exchange name (e.g., 'bingx', 'binance', 'bybit').
        name: User-friendly account name.
        is_demo: Whether this is a demo account (virtual tokens) or live account.
        api_key_hash: SHA-256 hash of API key for unique identification.
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "accounts"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to users
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Exchange and account info
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # API key identification (hash for security)
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    bot_state: Mapped["BotState | None"] = relationship(
        "BotState", back_populates="account", uselist=False
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "exchange", "name", "is_demo", name="uq_account"),
    )

    def __repr__(self) -> str:
        """String representation of Account."""
        mode = "demo" if self.is_demo else "live"
        return f"<Account(id={self.id}, exchange={self.exchange}, name={self.name}, mode={mode})>"
