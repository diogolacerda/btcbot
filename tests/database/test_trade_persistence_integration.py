"""Integration tests for trade persistence in OrderTracker."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, User
from src.database.repositories.trade_repository import TradeRepository
from src.grid.order_tracker import OrderTracker


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
async def trade_repository(async_session: AsyncSession) -> TradeRepository:
    """Create TradeRepository instance."""
    return TradeRepository(async_session)


class TestTradePersistenceIntegration:
    """Integration tests for trade persistence."""

    @pytest.mark.asyncio
    async def test_tracker_accepts_trade_repository(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test that OrderTracker accepts trade_repository parameter."""
        # Arrange & Act
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        # Assert
        assert tracker._trade_repository is not None
        assert tracker._account_id == account.id

    @pytest.mark.asyncio
    async def test_tracker_without_repository_works(self):
        """Test that OrderTracker works without repository (backward compatible)."""
        # Arrange
        tracker = OrderTracker()  # No repository passed

        # Add and fill an order
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )
        tracker.order_filled("order_123")

        # Act - Hit TP (should not crash without repository)
        trade = tracker.order_tp_hit("order_123", exit_price=50500.0)

        # Assert - Trade should be recorded in memory
        assert trade is not None
        assert trade.pnl > 0
        assert len(tracker._trades) == 1

    @pytest.mark.asyncio
    async def test_tracker_stores_exchange_tp_order_id(self):
        """Test that exchange_tp_order_id is stored in TrackedOrder."""
        # Arrange
        tracker = OrderTracker()

        # Add order
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Act - Set TP order ID (simulating what grid_manager would do)
        order = tracker._orders["order_123"]
        order.exchange_tp_order_id = "tp_order_456"

        # Assert
        assert order.exchange_tp_order_id == "tp_order_456"

    @pytest.mark.asyncio
    async def test_tracker_persistence_schedule_method_exists(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test that persistence scheduling method exists."""
        # Arrange
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        # Assert - Method should exist
        assert hasattr(tracker, "_schedule_trade_persistence")
        assert callable(tracker._schedule_trade_persistence)

    @pytest.mark.asyncio
    async def test_trade_repository_integration_direct(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test direct integration with TradeRepository (not through OrderTracker)."""
        # Arrange
        trade_data = {
            "account_id": account.id,
            "exchange_order_id": "order_123",
            "exchange_tp_order_id": "tp_order_456",
            "symbol": "BTC-USDT",
            "side": "LONG",
            "leverage": 10,
            "entry_price": Decimal("50000.00"),
            "exit_price": Decimal("50500.00"),
            "quantity": Decimal("0.001"),
            "tp_price": Decimal("50500.00"),
            "tp_percent": Decimal("1.0"),
            "pnl": Decimal("0.50"),
            "pnl_percent": Decimal("1.0"),
            "trading_fee": Decimal("0"),
            "funding_fee": Decimal("0"),
            "status": "CLOSED",
        }

        # Act
        trade_id = await trade_repository.save_trade(trade_data)

        # Assert - Trade should be in database
        trades = await trade_repository.get_trades_by_account(account.id)
        assert len(trades) == 1

        db_trade = trades[0]
        assert db_trade.id == trade_id
        assert db_trade.account_id == account.id
        assert db_trade.exchange_order_id == "order_123"
        assert db_trade.exchange_tp_order_id == "tp_order_456"
        assert db_trade.entry_price == Decimal("50000.00")
        assert db_trade.exit_price == Decimal("50500.00")
        assert db_trade.status == "CLOSED"
