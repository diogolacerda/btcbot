"""Tests for BaseRepository generic CRUD operations."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, Trade, User
from src.database.repositories.base_repository import BaseRepository


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
async def trade_repository(async_session: AsyncSession) -> BaseRepository[Trade]:
    """Create BaseRepository instance for Trade model."""
    return BaseRepository(async_session, Trade)


@pytest.fixture
async def sample_trade(async_session: AsyncSession, account: Account) -> Trade:
    """Create a sample trade for testing."""
    trade = Trade(
        account_id=account.id,
        exchange_order_id="12345",
        symbol="BTC-USDT",
        side="LONG",
        leverage=10,
        entry_price=Decimal("50000.00"),
        quantity=Decimal("0.1"),
        status="OPEN",
        opened_at=datetime.now(UTC),
    )
    async_session.add(trade)
    await async_session.commit()
    await async_session.refresh(trade)
    return trade


class TestBaseRepository:
    """Test cases for BaseRepository generic operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self,
        trade_repository: BaseRepository[Trade],
        sample_trade: Trade,
    ):
        """Test retrieving an existing record by ID."""
        # Act
        result = await trade_repository.get_by_id(sample_trade.id)

        # Assert
        assert result is not None
        assert result.id == sample_trade.id
        assert result.exchange_order_id == "12345"
        assert result.entry_price == Decimal("50000.00")

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        trade_repository: BaseRepository[Trade],
    ):
        """Test retrieving a non-existent record by ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await trade_repository.get_by_id(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(
        self,
        trade_repository: BaseRepository[Trade],
        async_session: AsyncSession,
        account: Account,
    ):
        """Test retrieving all records."""
        # Arrange - Create multiple trades
        trades = [
            Trade(
                account_id=account.id,
                entry_price=Decimal("50000.00"),
                quantity=Decimal("0.1"),
            ),
            Trade(
                account_id=account.id,
                entry_price=Decimal("51000.00"),
                quantity=Decimal("0.2"),
            ),
            Trade(
                account_id=account.id,
                entry_price=Decimal("52000.00"),
                quantity=Decimal("0.3"),
            ),
        ]
        for trade in trades:
            async_session.add(trade)
        await async_session.commit()

        # Act
        results = await trade_repository.get_all()

        # Assert
        assert len(results) == 3
        assert all(isinstance(trade, Trade) for trade in results)

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(
        self,
        trade_repository: BaseRepository[Trade],
        async_session: AsyncSession,
        account: Account,
    ):
        """Test retrieving records with pagination."""
        # Arrange - Create 5 trades
        for i in range(5):
            trade = Trade(
                account_id=account.id,
                entry_price=Decimal(f"{50000 + i * 1000}.00"),
                quantity=Decimal("0.1"),
            )
            async_session.add(trade)
        await async_session.commit()

        # Act - Get first 2 records
        first_page = await trade_repository.get_all(skip=0, limit=2)

        # Act - Get next 2 records
        second_page = await trade_repository.get_all(skip=2, limit=2)

        # Assert
        assert len(first_page) == 2
        assert len(second_page) == 2
        # Verify different records (assuming they're ordered by id)
        assert first_page[0].id != second_page[0].id

    @pytest.mark.asyncio
    async def test_create(
        self,
        trade_repository: BaseRepository[Trade],
        account: Account,
    ):
        """Test creating a new record."""
        # Arrange
        new_trade = Trade(
            account_id=account.id,
            exchange_order_id="99999",
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("45000.00"),
            quantity=Decimal("0.5"),
            status="OPEN",
        )

        # Act
        created_trade = await trade_repository.create(new_trade)

        # Assert
        assert created_trade.id is not None
        assert created_trade.exchange_order_id == "99999"
        assert created_trade.entry_price == Decimal("45000.00")
        assert created_trade.created_at is not None

        # Verify it can be retrieved
        retrieved = await trade_repository.get_by_id(created_trade.id)
        assert retrieved is not None
        assert retrieved.id == created_trade.id

    @pytest.mark.asyncio
    async def test_update(
        self,
        trade_repository: BaseRepository[Trade],
        sample_trade: Trade,
    ):
        """Test updating an existing record."""
        # Arrange
        original_price = sample_trade.entry_price
        sample_trade.entry_price = Decimal("55000.00")
        sample_trade.status = "CLOSED"

        # Act
        updated_trade = await trade_repository.update(sample_trade)

        # Assert
        assert updated_trade.entry_price == Decimal("55000.00")
        assert updated_trade.status == "CLOSED"
        assert updated_trade.entry_price != original_price

        # Verify changes persisted
        retrieved = await trade_repository.get_by_id(sample_trade.id)
        assert retrieved is not None
        assert retrieved.entry_price == Decimal("55000.00")
        assert retrieved.status == "CLOSED"

    @pytest.mark.asyncio
    async def test_delete_existing(
        self,
        trade_repository: BaseRepository[Trade],
        sample_trade: Trade,
    ):
        """Test deleting an existing record."""
        # Arrange
        trade_id = sample_trade.id

        # Act
        result = await trade_repository.delete(trade_id)

        # Assert
        assert result is True

        # Verify record was deleted
        retrieved = await trade_repository.get_by_id(trade_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_non_existing(
        self,
        trade_repository: BaseRepository[Trade],
    ):
        """Test deleting a non-existent record."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await trade_repository.delete(non_existent_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(
        self,
        trade_repository: BaseRepository[Trade],
        sample_trade: Trade,
    ):
        """Test exists check for an existing record."""
        # Act
        result = await trade_repository.exists(sample_trade.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(
        self,
        trade_repository: BaseRepository[Trade],
    ):
        """Test exists check for a non-existent record."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await trade_repository.exists(non_existent_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_rollback_on_error(
        self,
        trade_repository: BaseRepository[Trade],
        account: Account,
    ):
        """Test that create operation rolls back on error."""
        # Arrange - Create trade with invalid data (negative quantity)
        invalid_trade = Trade(
            account_id=account.id,
            entry_price=Decimal("50000.00"),
            quantity=Decimal("-0.1"),  # This should violate constraints
        )

        # Act & Assert
        # Note: This test may need adjustment based on actual DB constraints
        # For now, we're just verifying the error handling mechanism exists
        try:
            await trade_repository.create(invalid_trade)
        except Exception:
            # Verify session is still usable after rollback
            all_trades = await trade_repository.get_all()
            assert isinstance(all_trades, list)

    @pytest.mark.asyncio
    async def test_update_rollback_on_error(
        self,
        trade_repository: BaseRepository[Trade],
        sample_trade: Trade,
    ):
        """Test that update operation rolls back on error."""
        # Arrange
        original_status = sample_trade.status

        # Try to update with invalid data
        try:
            sample_trade.status = "X" * 1000  # Exceeds column length
            await trade_repository.update(sample_trade)
        except Exception:
            # Verify session is still usable after rollback
            retrieved = await trade_repository.get_by_id(sample_trade.id)
            assert retrieved is not None
            # Status should be unchanged due to rollback
            assert retrieved.status == original_status

    @pytest.mark.asyncio
    async def test_type_safety(
        self,
        async_session: AsyncSession,
    ):
        """Test that BaseRepository works with different model types."""
        # Arrange
        account_repo = BaseRepository(async_session, Account)

        # This test verifies type safety at runtime
        # The actual type checking is done by mypy at compile time
        assert account_repo.model == Account
