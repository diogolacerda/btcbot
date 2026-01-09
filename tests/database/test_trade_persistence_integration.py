"""Integration tests for trade persistence in OrderTracker."""

import asyncio
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, User
from src.database.repositories.trade_repository import TradeRepository
from src.grid.order_tracker import OrderTracker


async def wait_for_condition(condition_fn, timeout=2.0, poll_interval=0.01):
    """Wait for a condition to become true with polling.

    Args:
        condition_fn: Callable (sync or async) that returns True when condition is met
        timeout: Maximum time to wait in seconds (default: 2.0)
        poll_interval: Time between checks in seconds (default: 0.01)

    Raises:
        TimeoutError: If condition is not met within timeout
    """
    import inspect

    elapsed = 0.0
    while elapsed < timeout:
        # Check if condition_fn is async
        if inspect.iscoroutinefunction(condition_fn):
            result = await condition_fn()
        else:
            result = condition_fn()

        if result:
            return

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Condition not met within {timeout}s")


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

    @pytest.mark.asyncio
    async def test_open_trade_created_when_order_filled(
        self,
        trade_repository: TradeRepository,
        account: Account,
        async_session: AsyncSession,
    ):
        """Test that OPEN trade is created in database when order is filled."""
        # Arrange
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        # Add order
        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Act - Fill order (should create OPEN trade)
        tracker.order_filled("order_123")

        # Give background tasks a chance to start
        await asyncio.sleep(0.05)

        # Wait for async persistence to complete
        async def trade_persisted():
            trades = await trade_repository.get_open_trades(account.id)
            return len(trades) > 0

        await wait_for_condition(trade_persisted, timeout=2.0)

        # Assert - OPEN trade should exist in database
        open_trades = await trade_repository.get_open_trades(account.id)
        assert len(open_trades) == 1

        open_trade = open_trades[0]
        assert open_trade.status == "OPEN"
        assert open_trade.entry_price == Decimal("50000.00")
        assert open_trade.exit_price is None
        assert open_trade.pnl is None
        assert open_trade.closed_at is None

    @pytest.mark.asyncio
    async def test_trade_id_set_after_open_trade_created(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test that trade_id is set on TrackedOrder after OPEN trade is persisted."""
        # Arrange
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Act - Fill order
        order = tracker.order_filled("order_123")
        assert order is not None

        # Give background tasks a chance to start
        await asyncio.sleep(0.05)

        # Wait for async persistence to complete with active polling
        await wait_for_condition(
            lambda: order.trade_id is not None,
            timeout=2.0,
        )

        # Assert - trade_id should be set
        assert order.trade_id is not None
        assert isinstance(order.trade_id, type(account.id))  # UUID type

    @pytest.mark.asyncio
    async def test_open_trade_updated_when_tp_hit(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test that OPEN trade is updated to CLOSED when TP hits."""
        # Arrange
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Fill order (creates OPEN trade)
        order = tracker.order_filled("order_123")

        # Wait for OPEN trade to be persisted
        await wait_for_condition(
            lambda: order.trade_id is not None,
            timeout=2.0,
        )

        # Verify OPEN trade exists
        open_trades_before = await trade_repository.get_open_trades(account.id)
        assert len(open_trades_before) == 1
        trade_id_before = order.trade_id

        # Act - Hit TP (should update trade to CLOSED)
        tracker.order_tp_hit("order_123", exit_price=50500.0)

        # Give background tasks a chance to start
        await asyncio.sleep(0.05)

        # Wait for trade to be updated to CLOSED
        async def trade_closed():
            open_trades = await trade_repository.get_open_trades(account.id)
            return len(open_trades) == 0

        await wait_for_condition(trade_closed, timeout=2.0)

        # Assert - Trade should now be CLOSED, not OPEN
        open_trades_after = await trade_repository.get_open_trades(account.id)
        assert len(open_trades_after) == 0  # No more OPEN trades

        # Get the trade by ID
        closed_trade = await trade_repository.get_by_id(trade_id_before)
        assert closed_trade is not None
        assert closed_trade.status == "CLOSED"
        assert closed_trade.exit_price == Decimal("50500.0")
        assert closed_trade.pnl is not None
        assert closed_trade.pnl > 0
        assert closed_trade.closed_at is not None

    @pytest.mark.asyncio
    async def test_backward_compatible_closed_trade_without_open(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test backward compatibility: CLOSED trade created if no OPEN trade exists."""
        # Arrange - Tracker WITHOUT repository initially
        tracker = OrderTracker()

        tracker.add_order(
            order_id="order_123",
            entry_price=50000.0,
            tp_price=50500.0,
            quantity=0.001,
        )

        # Fill order without repository (no OPEN trade created)
        order = tracker.order_filled("order_123")
        assert order.trade_id is None  # No trade_id set

        # Now inject repository (simulating bot restart scenario)
        tracker._trade_repository = trade_repository
        tracker._account_id = account.id

        # Act - Hit TP (should create CLOSED trade directly, no OPEN state)
        tracker.order_tp_hit("order_123", exit_price=50500.0)

        # Give background tasks a chance to start
        await asyncio.sleep(0.05)

        # Wait for CLOSED trade to be persisted
        async def trade_persisted():
            trades = await trade_repository.get_trades_by_account(account.id)
            return len(trades) > 0

        await wait_for_condition(trade_persisted, timeout=2.0)

        # Assert - CLOSED trade should exist (created directly)
        all_trades = await trade_repository.get_trades_by_account(account.id)
        assert len(all_trades) == 1

        trade = all_trades[0]
        assert trade.status == "CLOSED"
        assert trade.exit_price == Decimal("50500.0")
        assert trade.pnl is not None

    @pytest.mark.asyncio
    async def test_schedule_open_trade_persistence_method_exists(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test that _schedule_open_trade_persistence method exists."""
        # Arrange
        tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account.id,
        )

        # Assert - Method should exist
        assert hasattr(tracker, "_schedule_open_trade_persistence")
        assert callable(tracker._schedule_open_trade_persistence)
