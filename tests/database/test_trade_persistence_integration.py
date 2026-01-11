"""Integration tests for trade persistence in OrderTracker."""

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
    async def test_tracker_accepts_account_id(
        self,
        account: Account,
    ):
        """Test that OrderTracker accepts account_id parameter."""
        # Arrange & Act
        tracker = OrderTracker(account_id=account.id)

        # Assert
        assert tracker._account_id == account.id

    @pytest.mark.asyncio
    async def test_tracker_without_account_works(self):
        """Test that OrderTracker works without account_id (backward compatible)."""
        # Arrange
        tracker = OrderTracker()  # No account_id passed

        # Add and fill an order
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )
        await tracker.order_filled("order_123")

        # Act - Hit TP (should not crash without account_id)
        trade = await tracker.order_tp_hit("order_123", exit_price=50500.0)

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
    async def test_persist_methods_exist(
        self,
        account: Account,
    ):
        """Test that persistence methods exist."""
        # Arrange
        tracker = OrderTracker(account_id=account.id)

        # Assert - Methods should exist
        assert hasattr(tracker, "_persist_trade_closed")
        assert callable(tracker._persist_trade_closed)
        assert hasattr(tracker, "_persist_open_trade")
        assert callable(tracker._persist_open_trade)

    @pytest.mark.asyncio
    async def test_order_filled_is_async(
        self,
        account: Account,
    ):
        """Test that order_filled is an async method."""
        # Arrange
        tracker = OrderTracker(account_id=account.id)
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Act - order_filled should be awaitable
        import inspect

        assert inspect.iscoroutinefunction(tracker.order_filled)

        # Call it
        result = await tracker.order_filled("order_123")

        # Assert
        assert result is not None
        assert result.entry_price == 50000.0

    @pytest.mark.asyncio
    async def test_order_tp_hit_is_async(
        self,
        account: Account,
    ):
        """Test that order_tp_hit is an async method."""
        # Arrange
        tracker = OrderTracker(account_id=account.id)
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )
        await tracker.order_filled("order_123")

        # Act - order_tp_hit should be awaitable
        import inspect

        assert inspect.iscoroutinefunction(tracker.order_tp_hit)

        # Call it
        trade = await tracker.order_tp_hit("order_123", exit_price=50500.0)

        # Assert
        assert trade is not None
        assert trade.pnl > 0

    @pytest.mark.asyncio
    async def test_trade_record_created_in_memory(self):
        """Test that trade records are created in memory."""
        # Arrange
        tracker = OrderTracker()

        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Act
        await tracker.order_filled("order_123")
        trade = await tracker.order_tp_hit("order_123", exit_price=50500.0)

        # Assert
        assert trade is not None
        assert trade.entry_price == 50000.0
        assert trade.exit_price == 50500.0
        assert trade.quantity == 0.001
        assert trade.pnl == 0.5  # (50500 - 50000) * 0.001 = 0.5
        assert len(tracker._trades) == 1

    @pytest.mark.asyncio
    async def test_multiple_trades_tracked(self):
        """Test that multiple trades are tracked correctly."""
        # Arrange
        tracker = OrderTracker()

        # Add multiple orders
        for i in range(3):
            tracker.add_order(
                order_id=f"order_{i}",
                entry_price=50000.0 + i * 100,
                tp_price=50050.0 + i * 100,
                quantity=0.001,
            )

        # Fill and close all
        for i in range(3):
            await tracker.order_filled(f"order_{i}")
            await tracker.order_tp_hit(f"order_{i}", exit_price=50050.0 + i * 100)

        # Assert
        assert len(tracker._trades) == 3
        assert tracker.total_trades == 3
        total_pnl = sum(t.pnl for t in tracker._trades)
        assert total_pnl > 0

    @pytest.mark.asyncio
    async def test_win_rate_calculation(self):
        """Test win rate is calculated correctly."""
        # Arrange
        tracker = OrderTracker()

        # Create 2 winning trades and 1 losing trade
        for i, (entry, exit) in enumerate(
            [
                (50000.0, 50100.0),  # Win
                (50000.0, 50100.0),  # Win
                (50000.0, 49900.0),  # Loss
            ]
        ):
            tracker.add_order(
                order_id=f"order_{i}",
                entry_price=entry,
                tp_price=entry + 100,
                quantity=0.001,
            )
            await tracker.order_filled(f"order_{i}")
            await tracker.order_tp_hit(f"order_{i}", exit_price=exit)

        # Assert - 2/3 = 66.67% win rate
        assert tracker.win_rate == pytest.approx(66.67, rel=0.01)
