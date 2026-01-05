"""Tests for ActivityEventRepository."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, EventType, User
from src.database.repositories import ActivityEventRepository


@pytest.fixture
async def user(async_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",  # pragma: allowlist secret
        name="Test User",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def account(async_session: AsyncSession, user: User) -> Account:
    """Create a test account."""
    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    async_session.add(account)
    await async_session.commit()
    await async_session.refresh(account)
    return account


@pytest.fixture
async def repository(async_session: AsyncSession) -> ActivityEventRepository:
    """Create ActivityEventRepository instance."""
    return ActivityEventRepository(async_session)


class TestActivityEventRepository:
    """Test cases for ActivityEventRepository."""

    @pytest.mark.asyncio
    async def test_create_event(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test creating a new activity event."""
        # Act
        event = await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Order filled at $100,000",
            event_data={"order_id": "12345", "price": 100000},
        )

        # Assert
        assert event is not None
        assert event.account_id == account.id
        assert event.event_type == "ORDER_FILLED"
        assert event.description == "Order filled at $100,000"
        assert event.event_data == {"order_id": "12345", "price": 100000}
        assert event.timestamp is not None

    @pytest.mark.asyncio
    async def test_create_event_with_string_type(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test creating event with string event type."""
        # Act
        event = await repository.create_event(
            account_id=account.id,
            event_type="CUSTOM_EVENT",
            description="Custom event occurred",
        )

        # Assert
        assert event.event_type == "CUSTOM_EVENT"

    @pytest.mark.asyncio
    async def test_create_event_with_custom_timestamp(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test creating event with custom timestamp."""
        # Arrange
        custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        # Act
        event = await repository.create_event(
            account_id=account.id,
            event_type=EventType.TRADE_CLOSED,
            description="Trade closed",
            timestamp=custom_time,
        )

        # Assert - compare without timezone (SQLite doesn't preserve timezone)
        assert event.timestamp.replace(tzinfo=None) == custom_time.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_get_events_by_account(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test getting events for an account."""
        # Arrange - Create multiple events
        for i in range(5):
            await repository.create_event(
                account_id=account.id,
                event_type=EventType.ORDER_FILLED,
                description=f"Event {i}",
            )

        # Act
        events = await repository.get_events_by_account(account.id)

        # Assert
        assert len(events) == 5
        # All events should be present (order depends on timestamp which may be same)
        descriptions = {e.description for e in events}
        assert descriptions == {"Event 0", "Event 1", "Event 2", "Event 3", "Event 4"}

    @pytest.mark.asyncio
    async def test_get_events_by_account_with_pagination(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test pagination of events."""
        # Arrange
        for i in range(10):
            await repository.create_event(
                account_id=account.id,
                event_type=EventType.ORDER_FILLED,
                description=f"Event {i}",
            )

        # Act
        page1 = await repository.get_events_by_account(account.id, limit=3, offset=0)
        page2 = await repository.get_events_by_account(account.id, limit=3, offset=3)

        # Assert
        assert len(page1) == 3
        assert len(page2) == 3
        # Pages should not overlap
        page1_ids = {e.id for e in page1}
        page2_ids = {e.id for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_get_events_by_period(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test filtering events by time period."""
        # Arrange
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)

        # Create event in period
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Recent event",
            timestamp=now - timedelta(hours=12),
        )

        # Create event outside period
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Old event",
            timestamp=last_week - timedelta(days=1),
        )

        # Act
        events = await repository.get_events_by_period(
            account_id=account.id,
            start=yesterday,
            end=now,
        )

        # Assert
        assert len(events) == 1
        assert events[0].description == "Recent event"

    @pytest.mark.asyncio
    async def test_get_events_by_type(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test filtering events by type."""
        # Arrange
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Order event",
        )
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.TRADE_CLOSED,
            description="Trade event",
        )
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Another order event",
        )

        # Act
        events = await repository.get_events_by_type(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
        )

        # Assert
        assert len(events) == 2
        assert all(e.event_type == "ORDER_FILLED" for e in events)

    @pytest.mark.asyncio
    async def test_count_events_by_account(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test counting events for an account."""
        # Arrange
        for i in range(7):
            await repository.create_event(
                account_id=account.id,
                event_type=EventType.ORDER_FILLED,
                description=f"Event {i}",
            )

        # Act
        count = await repository.count_events_by_account(account.id)

        # Assert
        assert count == 7

    @pytest.mark.asyncio
    async def test_delete_old_events(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test deleting old events."""
        # Arrange
        now = datetime.now(UTC)

        # Create recent event
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Recent",
            timestamp=now,
        )

        # Create old event
        await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Old",
            timestamp=now - timedelta(days=30),
        )

        # Act
        deleted_count = await repository.delete_old_events(
            account_id=account.id,
            older_than=now - timedelta(days=7),
        )

        # Assert
        assert deleted_count == 1
        remaining = await repository.get_events_by_account(account.id)
        assert len(remaining) == 1
        assert remaining[0].description == "Recent"

    @pytest.mark.asyncio
    async def test_events_isolated_by_account(
        self,
        repository: ActivityEventRepository,
        async_session: AsyncSession,
        user: User,
    ):
        """Test that events are isolated between accounts."""
        # Arrange - Create two accounts
        account1 = Account(
            user_id=user.id,
            exchange="bingx",
            name="Account 1",
            is_demo=True,
        )
        account2 = Account(
            user_id=user.id,
            exchange="bingx",
            name="Account 2",
            is_demo=True,
        )
        async_session.add_all([account1, account2])
        await async_session.commit()

        # Create events for each account
        await repository.create_event(
            account_id=account1.id,
            event_type=EventType.ORDER_FILLED,
            description="Account 1 event",
        )
        await repository.create_event(
            account_id=account2.id,
            event_type=EventType.ORDER_FILLED,
            description="Account 2 event",
        )

        # Act
        events1 = await repository.get_events_by_account(account1.id)
        events2 = await repository.get_events_by_account(account2.id)

        # Assert
        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0].description == "Account 1 event"
        assert events2[0].description == "Account 2 event"


class TestActivityEventModel:
    """Test cases for ActivityEvent model."""

    @pytest.mark.asyncio
    async def test_event_repr(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test string representation of ActivityEvent."""
        # Arrange
        event = await repository.create_event(
            account_id=account.id,
            event_type=EventType.ORDER_FILLED,
            description="Test event",
        )

        # Act
        repr_str = repr(event)

        # Assert
        assert "ActivityEvent" in repr_str
        assert str(event.id) in repr_str
        assert "ORDER_FILLED" in repr_str

    @pytest.mark.asyncio
    async def test_all_event_types(
        self,
        repository: ActivityEventRepository,
        account: Account,
    ):
        """Test that all EventType values can be stored."""
        # Act & Assert
        for event_type in EventType:
            event = await repository.create_event(
                account_id=account.id,
                event_type=event_type,
                description=f"Test {event_type.value}",
            )
            assert event.event_type == event_type.value
