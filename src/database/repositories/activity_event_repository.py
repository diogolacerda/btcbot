"""Activity event repository for managing activity event records."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.activity_event import ActivityEvent, EventType
from src.database.repositories.base_repository import BaseRepository
from src.utils.logger import main_logger


class ActivityEventRepository(BaseRepository[ActivityEvent]):
    """Repository for ActivityEvent CRUD operations.

    Inherits from BaseRepository to leverage common CRUD operations
    while providing activity-event-specific methods.

    Provides async methods for creating, reading, and filtering activity events
    for the dashboard timeline.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, ActivityEvent)

    async def create_event(
        self,
        account_id: UUID,
        event_type: EventType | str,
        description: str,
        event_data: dict | None = None,
        timestamp: datetime | None = None,
    ) -> ActivityEvent:
        """Create a new activity event.

        Args:
            account_id: Account UUID.
            event_type: Type of event (EventType enum or string).
            description: Human-readable description of the event.
            event_data: Optional additional event data as dictionary.
            timestamp: Event timestamp (defaults to now if not provided).

        Returns:
            Created ActivityEvent instance.

        Raises:
            Exception: If database operation fails.
        """
        try:
            # Convert EventType enum to string if needed
            event_type_str = event_type.value if isinstance(event_type, EventType) else event_type

            event = ActivityEvent(
                account_id=account_id,
                event_type=event_type_str,
                description=description,
                event_data=event_data,
            )

            if timestamp:
                event.timestamp = timestamp

            created_event = await super().create(event)
            main_logger.debug(f"Activity event created: {event_type_str} for account {account_id}")
            return created_event

        except Exception as e:
            main_logger.error(f"Error creating activity event: {e}")
            raise

    async def get_events_by_account(
        self,
        account_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityEvent]:
        """Get activity events for an account with pagination.

        Args:
            account_id: Account UUID.
            limit: Maximum number of events to return (default: 50).
            offset: Number of events to skip.

        Returns:
            List of ActivityEvent instances ordered by timestamp DESC.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = (
                select(ActivityEvent)
                .where(ActivityEvent.account_id == account_id)
                .order_by(ActivityEvent.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            main_logger.error(f"Error fetching activity events for account {account_id}: {e}")
            raise

    async def get_events_by_period(
        self,
        account_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[ActivityEvent]:
        """Get activity events for an account within a time period.

        Args:
            account_id: Account UUID.
            start: Start datetime (inclusive).
            end: End datetime (inclusive).
            limit: Maximum number of events to return.

        Returns:
            List of ActivityEvent instances in the specified period.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = (
                select(ActivityEvent)
                .where(
                    ActivityEvent.account_id == account_id,
                    ActivityEvent.timestamp >= start,
                    ActivityEvent.timestamp <= end,
                )
                .order_by(ActivityEvent.timestamp.desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            main_logger.error(
                f"Error fetching activity events for account {account_id} "
                f"in period {start} - {end}: {e}"
            )
            raise

    async def get_events_by_type(
        self,
        account_id: UUID,
        event_type: EventType | str,
        limit: int = 50,
    ) -> list[ActivityEvent]:
        """Get activity events of a specific type for an account.

        Args:
            account_id: Account UUID.
            event_type: Type of event to filter by.
            limit: Maximum number of events to return.

        Returns:
            List of ActivityEvent instances of the specified type.

        Raises:
            Exception: If database operation fails.
        """
        try:
            event_type_str = event_type.value if isinstance(event_type, EventType) else event_type

            stmt = (
                select(ActivityEvent)
                .where(
                    ActivityEvent.account_id == account_id,
                    ActivityEvent.event_type == event_type_str,
                )
                .order_by(ActivityEvent.timestamp.desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            main_logger.error(
                f"Error fetching activity events of type {event_type} for account {account_id}: {e}"
            )
            raise

    async def count_events_by_account(self, account_id: UUID) -> int:
        """Count total activity events for an account.

        Args:
            account_id: Account UUID.

        Returns:
            Total number of events.

        Raises:
            Exception: If database operation fails.
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count()).where(ActivityEvent.account_id == account_id)
            result = await self.session.execute(stmt)
            count: int = result.scalar() or 0
            return count

        except Exception as e:
            main_logger.error(f"Error counting activity events for account {account_id}: {e}")
            raise

    async def delete_old_events(
        self,
        account_id: UUID,
        older_than: datetime,
    ) -> int:
        """Delete activity events older than a specified date.

        Useful for cleanup/retention policies.

        Args:
            account_id: Account UUID.
            older_than: Delete events with timestamp before this datetime.

        Returns:
            Number of events deleted.

        Raises:
            Exception: If database operation fails.
        """
        try:
            from sqlalchemy import delete

            stmt = delete(ActivityEvent).where(
                ActivityEvent.account_id == account_id,
                ActivityEvent.timestamp < older_than,
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count: int = getattr(result, "rowcount", 0) or 0
            main_logger.info(
                f"Deleted {deleted_count} old activity events for account {account_id}"
            )
            return deleted_count

        except Exception as e:
            main_logger.error(f"Error deleting old activity events: {e}")
            raise
