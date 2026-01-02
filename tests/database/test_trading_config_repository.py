"""Tests for TradingConfigRepository."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models.account import Account
from src.database.models.user import User
from src.database.repositories.trading_config_repository import TradingConfigRepository


@pytest.fixture
async def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[arg-type, call-overload]

    async with async_session() as session:  # type: ignore[misc]
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
async def repository(db_session: AsyncSession):
    """Create repository instance."""
    return TradingConfigRepository(db_session)


class TestTradingConfigRepository:
    """Test suite for TradingConfigRepository."""

    @pytest.mark.asyncio
    async def test_create_or_update_creates_new_config(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test creating a new trading config."""
        config = await repository.create_or_update(
            account_id=test_account.id,
            symbol="BTC-USDT",
            leverage=15,
            order_size_usdt=Decimal("200.00"),
            margin_mode="CROSSED",
            take_profit_percent=Decimal("1.5"),
        )

        assert config.account_id == test_account.id
        assert config.symbol == "BTC-USDT"
        assert config.leverage == 15
        assert config.order_size_usdt == Decimal("200.00")
        assert config.margin_mode == "CROSSED"
        assert config.take_profit_percent == Decimal("1.5")

    @pytest.mark.asyncio
    async def test_create_or_update_uses_defaults(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test creating config with default values."""
        config = await repository.create_or_update(account_id=test_account.id)

        assert config.account_id == test_account.id
        assert config.symbol == "BTC-USDT"
        assert config.leverage == 10
        assert config.order_size_usdt == Decimal("100.00")
        assert config.margin_mode == "CROSSED"
        assert config.take_profit_percent == Decimal("0.50")

    @pytest.mark.asyncio
    async def test_create_or_update_updates_existing(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test updating an existing trading config."""
        # Create initial config
        config1 = await repository.create_or_update(
            account_id=test_account.id,
            leverage=10,
        )

        # Update config
        config2 = await repository.create_or_update(
            account_id=test_account.id,
            leverage=20,
        )

        assert config1.id == config2.id  # Same config
        assert config2.leverage == 20  # Updated value

    @pytest.mark.asyncio
    async def test_get_by_account(self, repository: TradingConfigRepository, test_account: Account):
        """Test getting config by account ID."""
        # Create config
        await repository.create_or_update(
            account_id=test_account.id,
            symbol="ETH-USDT",
        )

        # Retrieve config
        config = await repository.get_by_account(test_account.id)

        assert config is not None
        assert config.account_id == test_account.id
        assert config.symbol == "ETH-USDT"

    @pytest.mark.asyncio
    async def test_get_by_account_not_found(self, repository: TradingConfigRepository):
        """Test getting config for non-existent account."""
        config = await repository.get_by_account(uuid4())
        assert config is None

    @pytest.mark.asyncio
    async def test_update_config(self, repository: TradingConfigRepository, test_account: Account):
        """Test updating specific config fields."""
        # Create config
        await repository.create_or_update(account_id=test_account.id)

        # Update specific fields
        config = await repository.update_config(
            test_account.id,
            leverage=25,
            take_profit_percent=Decimal("2.0"),
        )

        assert config.leverage == 25
        assert config.take_profit_percent == Decimal("2.0")
        # Other fields should remain default
        assert config.symbol == "BTC-USDT"
        assert config.order_size_usdt == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_update_config_not_found(self, repository: TradingConfigRepository):
        """Test updating config for non-existent account."""
        with pytest.raises(Exception, match="No trading config found"):
            await repository.update_config(
                uuid4(),
                leverage=15,
            )

    @pytest.mark.asyncio
    async def test_partial_update_with_create_or_update(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test partial update using create_or_update."""
        # Create initial config
        await repository.create_or_update(
            account_id=test_account.id,
            symbol="BTC-USDT",
            leverage=10,
            order_size_usdt=Decimal("100.00"),
        )

        # Update only leverage
        config = await repository.create_or_update(
            account_id=test_account.id,
            leverage=20,
        )

        # Updated field
        assert config.leverage == 20
        # Unchanged fields
        assert config.symbol == "BTC-USDT"
        assert config.order_size_usdt == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_inherited_crud_methods(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test methods inherited from BaseRepository."""
        # Create config
        config = await repository.create_or_update(account_id=test_account.id)

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
    async def test_dynamic_tp_default_values(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test that Dynamic TP fields have correct default values (BE-035)."""
        config = await repository.create_or_update(account_id=test_account.id)

        # Verify Dynamic TP defaults
        assert config.tp_dynamic_enabled is False
        assert config.tp_base_percent == Decimal("0.30")
        assert config.tp_min_percent == Decimal("0.30")
        assert config.tp_max_percent == Decimal("1.00")
        assert config.tp_safety_margin == Decimal("0.05")
        assert config.tp_check_interval_min == 60

    @pytest.mark.asyncio
    async def test_create_config_with_dynamic_tp_values(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test creating config with custom Dynamic TP values (BE-035)."""
        config = await repository.create_or_update(
            account_id=test_account.id,
            tp_dynamic_enabled=True,
            tp_base_percent=Decimal("0.40"),
            tp_min_percent=Decimal("0.35"),
            tp_max_percent=Decimal("1.50"),
            tp_safety_margin=Decimal("0.10"),
            tp_check_interval_min=120,
        )

        assert config.tp_dynamic_enabled is True
        assert config.tp_base_percent == Decimal("0.40")
        assert config.tp_min_percent == Decimal("0.35")
        assert config.tp_max_percent == Decimal("1.50")
        assert config.tp_safety_margin == Decimal("0.10")
        assert config.tp_check_interval_min == 120

    @pytest.mark.asyncio
    async def test_update_dynamic_tp_using_create_or_update(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test updating Dynamic TP fields using create_or_update (BE-035)."""
        # Create with defaults
        config1 = await repository.create_or_update(account_id=test_account.id)
        assert config1.tp_dynamic_enabled is False

        # Update Dynamic TP enabled
        config2 = await repository.create_or_update(
            account_id=test_account.id,
            tp_dynamic_enabled=True,
            tp_base_percent=Decimal("0.50"),
        )

        assert config1.id == config2.id  # Same config
        assert config2.tp_dynamic_enabled is True
        assert config2.tp_base_percent == Decimal("0.50")
        # Other TP fields should remain default
        assert config2.tp_min_percent == Decimal("0.30")
        assert config2.tp_max_percent == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_update_dynamic_tp_using_update_config(
        self, repository: TradingConfigRepository, test_account: Account
    ):
        """Test updating Dynamic TP fields using update_config (BE-035)."""
        # Create with defaults
        await repository.create_or_update(account_id=test_account.id)

        # Update specific Dynamic TP fields
        config = await repository.update_config(
            test_account.id,
            tp_dynamic_enabled=True,
            tp_min_percent=Decimal("0.40"),
            tp_max_percent=Decimal("2.00"),
            tp_check_interval_min=90,
        )

        assert config.tp_dynamic_enabled is True
        assert config.tp_min_percent == Decimal("0.40")
        assert config.tp_max_percent == Decimal("2.00")
        assert config.tp_check_interval_min == 90
        # Unchanged TP fields
        assert config.tp_base_percent == Decimal("0.30")
        assert config.tp_safety_margin == Decimal("0.05")
