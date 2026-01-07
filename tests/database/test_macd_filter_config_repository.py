"""Tests for MACDFilterConfigRepository."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models.account import Account
from src.database.models.strategy import Strategy
from src.database.models.user import User
from src.database.repositories.macd_filter_config_repository import MACDFilterConfigRepository


@pytest.fixture
async def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(email="test@example.com", password_hash="hashedpassword123", name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_account(db_session: AsyncSession, test_user: User):
    """Create a test account."""
    account = Account(
        user_id=test_user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


@pytest.fixture
async def test_strategy(db_session: AsyncSession, test_account: Account):
    """Create a test strategy."""
    strategy = Strategy(
        account_id=test_account.id,
        name="Test Strategy",
        is_active=False,
        symbol="BTC-USDT",
    )
    db_session.add(strategy)
    await db_session.commit()
    await db_session.refresh(strategy)
    return strategy


@pytest.fixture
async def repository(db_session: AsyncSession):
    """Create repository instance."""
    return MACDFilterConfigRepository(db_session)


class TestMACDFilterConfigRepository:
    """Test suite for MACDFilterConfigRepository."""

    @pytest.mark.asyncio
    async def test_create_or_update_creates_new_config(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test creating a new MACD filter config."""
        config = await repository.create_or_update(
            strategy_id=test_strategy.id,
            enabled=True,
            fast_period=15,
            slow_period=30,
            signal_period=10,
            timeframe="4h",
        )

        assert config.strategy_id == test_strategy.id
        assert config.enabled is True
        assert config.fast_period == 15
        assert config.slow_period == 30
        assert config.signal_period == 10
        assert config.timeframe == "4h"

    @pytest.mark.asyncio
    async def test_create_or_update_uses_defaults(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test creating config with default values."""
        config = await repository.create_or_update(strategy_id=test_strategy.id)

        assert config.strategy_id == test_strategy.id
        assert config.enabled is True
        assert config.fast_period == 12
        assert config.slow_period == 26
        assert config.signal_period == 9
        assert config.timeframe == "1h"

    @pytest.mark.asyncio
    async def test_create_or_update_updates_existing(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test updating an existing MACD filter config."""
        # Create initial config
        config1 = await repository.create_or_update(
            strategy_id=test_strategy.id,
            fast_period=12,
        )

        # Update config
        config2 = await repository.create_or_update(
            strategy_id=test_strategy.id,
            fast_period=15,
        )

        assert config1.id == config2.id
        assert config2.fast_period == 15

    @pytest.mark.asyncio
    async def test_get_by_strategy(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test getting config by strategy ID."""
        # Create config
        await repository.create_or_update(
            strategy_id=test_strategy.id,
            timeframe="15m",
        )

        # Retrieve config
        config = await repository.get_by_strategy(test_strategy.id)

        assert config is not None
        assert config.strategy_id == test_strategy.id
        assert config.timeframe == "15m"

    @pytest.mark.asyncio
    async def test_get_by_strategy_not_found(self, repository: MACDFilterConfigRepository):
        """Test getting config for non-existent strategy."""
        config = await repository.get_by_strategy(uuid4())
        assert config is None

    @pytest.mark.asyncio
    async def test_update_config(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test updating specific config fields."""
        # Create config
        await repository.create_or_update(strategy_id=test_strategy.id)

        # Update specific fields
        config = await repository.update_config(
            test_strategy.id,
            fast_period=20,
            signal_period=12,
        )

        assert config.fast_period == 20
        assert config.signal_period == 12
        # Other fields should remain default
        assert config.slow_period == 26
        assert config.timeframe == "1h"

    @pytest.mark.asyncio
    async def test_update_config_not_found(self, repository: MACDFilterConfigRepository):
        """Test updating config for non-existent strategy."""
        with pytest.raises(Exception, match="No MACD filter config found"):
            await repository.update_config(
                uuid4(),
                fast_period=15,
            )

    @pytest.mark.asyncio
    async def test_partial_update_with_create_or_update(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test partial update using create_or_update."""
        # Create initial config
        await repository.create_or_update(
            strategy_id=test_strategy.id,
            enabled=True,
            fast_period=12,
            slow_period=26,
        )

        # Update only fast_period
        config = await repository.create_or_update(
            strategy_id=test_strategy.id,
            fast_period=15,
        )

        # Updated field
        assert config.fast_period == 15
        # Unchanged fields
        assert config.enabled is True
        assert config.slow_period == 26

    @pytest.mark.asyncio
    async def test_inherited_crud_methods(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test methods inherited from BaseRepository."""
        # Create config
        config = await repository.create_or_update(strategy_id=test_strategy.id)

        # Test get_by_id
        retrieved = await repository.get_by_id(config.id)
        assert retrieved is not None
        assert retrieved.id == config.id

        # Test exists
        assert await repository.exists(config.id) is True
        assert await repository.exists(uuid4()) is False

        # Test delete
        assert await repository.delete(config.id) is True
        assert await repository.get_by_id(config.id) is None

    @pytest.mark.asyncio
    async def test_create_config_disabled(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test creating config with enabled=False."""
        config = await repository.create_or_update(
            strategy_id=test_strategy.id,
            enabled=False,
        )

        assert config.enabled is False

    @pytest.mark.asyncio
    async def test_update_enabled_field(
        self, repository: MACDFilterConfigRepository, test_strategy: Strategy
    ):
        """Test updating the enabled field."""
        # Create with enabled=True
        config1 = await repository.create_or_update(
            strategy_id=test_strategy.id,
            enabled=True,
        )
        assert config1.enabled is True

        # Update to disabled
        config2 = await repository.create_or_update(
            strategy_id=test_strategy.id,
            enabled=False,
        )

        assert config1.id == config2.id
        assert config2.enabled is False

    @pytest.mark.asyncio
    async def test_multiple_strategies_with_different_configs(
        self,
        db_session: AsyncSession,
        test_account: Account,
        repository: MACDFilterConfigRepository,
    ):
        """Test that multiple strategies can have different MACD configs."""
        # Create a second account for the second strategy
        account2 = Account(
            user_id=test_account.user_id,
            exchange="bingx",
            name="Test Account 2",
            is_demo=True,
        )
        db_session.add(account2)
        await db_session.commit()
        await db_session.refresh(account2)

        # Create two strategies on different accounts
        strategy1 = Strategy(
            account_id=test_account.id,
            name="Strategy 1",
            is_active=False,
            symbol="BTC-USDT",
        )
        strategy2 = Strategy(
            account_id=account2.id,
            name="Strategy 2",
            is_active=False,
            symbol="ETH-USDT",
        )
        db_session.add(strategy1)
        db_session.add(strategy2)
        await db_session.commit()
        await db_session.refresh(strategy1)
        await db_session.refresh(strategy2)

        # Create different configs
        config1 = await repository.create_or_update(
            strategy_id=strategy1.id,
            fast_period=12,
            timeframe="1h",
        )
        config2 = await repository.create_or_update(
            strategy_id=strategy2.id,
            fast_period=20,
            timeframe="4h",
        )

        # Verify they are independent
        assert config1.strategy_id == strategy1.id
        assert config1.fast_period == 12
        assert config1.timeframe == "1h"

        assert config2.strategy_id == strategy2.id
        assert config2.fast_period == 20
        assert config2.timeframe == "4h"

        # Verify retrieval
        retrieved1 = await repository.get_by_strategy(strategy1.id)
        retrieved2 = await repository.get_by_strategy(strategy2.id)

        assert retrieved1.id == config1.id
        assert retrieved2.id == config2.id
