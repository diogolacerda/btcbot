"""Activity event model for storing timeline events."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base

# Use JSONB on PostgreSQL, JSON on other databases (like SQLite for tests)
JSONType = JSON().with_variant(JSONB(), "postgresql")


class EventType(str, Enum):
    """Types of activity events that can be recorded."""

    ORDER_FILLED = "ORDER_FILLED"
    TRADE_CLOSED = "TRADE_CLOSED"
    STRATEGY_PAUSED = "STRATEGY_PAUSED"
    STRATEGY_RESUMED = "STRATEGY_RESUMED"
    TP_ADJUSTED = "TP_ADJUSTED"
    CYCLE_ACTIVATED = "CYCLE_ACTIVATED"
    CYCLE_DEACTIVATED = "CYCLE_DEACTIVATED"
    BOT_STARTED = "BOT_STARTED"
    BOT_STOPPED = "BOT_STOPPED"
    ERROR_OCCURRED = "ERROR_OCCURRED"


class ActivityEvent(Base):
    """Activity event model for storing timeline events.

    Records significant events that occur during bot operation, such as
    order fills, trade closures, strategy changes, and system events.
    Used for displaying an activity timeline in the dashboard.

    Attributes:
        id: Unique event identifier (UUID).
        account_id: FK reference to accounts table.
        event_type: Type of event (from EventType enum).
        description: Human-readable description of the event.
        event_data: Additional event-specific data as JSON.
        timestamp: When the event occurred.
        created_at: When the record was created.
    """

    __tablename__ = "activity_events"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts
    account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # Event data
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    event_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True, default=None)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_activity_events_account_timestamp", "account_id", "timestamp"),
        Index(
            "idx_activity_events_account_timestamp_desc",
            "account_id",
            timestamp.desc(),
        ),
        Index("idx_activity_events_event_type", "event_type"),
        Index("idx_activity_events_account_type", "account_id", "event_type"),
    )

    def __repr__(self) -> str:
        """String representation of ActivityEvent."""
        return (
            f"<ActivityEvent(id={self.id}, account_id={self.account_id}, "
            f"event_type={self.event_type}, timestamp={self.timestamp})>"
        )
