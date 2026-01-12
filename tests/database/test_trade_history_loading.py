"""Tests for trade history loading functionality."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, User
from src.database.models.trade import Trade
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


class TestTradeHistoryLoading:
    """Tests for loading trade history into OrderTracker."""

    @pytest.mark.asyncio
    async def test_load_empty_history(self):
        """Test loading with no trades."""
        # Arrange
        tracker = OrderTracker()

        # Act
        stats = tracker.load_trade_history([])

        # Assert
        assert stats["trades_loaded"] == 0
        assert stats["total_pnl"] == 0.0
        assert stats["win_rate"] == 0.0
        assert stats["date_range"] is None
        assert tracker.total_trades == 0

    @pytest.mark.asyncio
    async def test_load_valid_trades(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test loading valid closed trades."""
        # Arrange
        tracker = OrderTracker()
        now = datetime.now(UTC)

        # Create mock Trade objects
        trades = []
        for i in range(3):
            trade = Trade(
                account_id=account.id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("50000.00") + Decimal(i * 100),
                exit_price=Decimal("50500.00") + Decimal(i * 100),
                quantity=Decimal("0.001"),
                tp_price=Decimal("50500.00") + Decimal(i * 100),
                pnl=Decimal("0.50") + Decimal(i * 0.1),
                status="CLOSED",
                opened_at=now,
                closed_at=now,
            )
            async_session.add(trade)
            trades.append(trade)

        await async_session.commit()
        for trade in trades:
            await async_session.refresh(trade)

        # Act
        stats = tracker.load_trade_history(trades)

        # Assert
        assert stats["trades_loaded"] == 3
        assert tracker.total_trades == 3
        assert stats["total_pnl"] > 0
        assert stats["win_rate"] == 100.0  # All positive PnL
        assert stats["date_range"] is not None

    @pytest.mark.asyncio
    async def test_load_trades_with_wins_and_losses(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test win rate calculation with mixed results."""
        # Arrange
        tracker = OrderTracker()
        now = datetime.now(UTC)

        trades = []
        # 2 wins
        for _ in range(2):
            trade = Trade(
                account_id=account.id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("50000.00"),
                exit_price=Decimal("50500.00"),
                quantity=Decimal("0.001"),
                pnl=Decimal("0.50"),  # Win
                status="CLOSED",
                opened_at=now,
                closed_at=now,
            )
            async_session.add(trade)
            trades.append(trade)

        # 1 loss
        trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("49500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("-0.50"),  # Loss
            status="CLOSED",
            opened_at=now,
            closed_at=now,
        )
        async_session.add(trade)
        trades.append(trade)

        await async_session.commit()
        for trade in trades:
            await async_session.refresh(trade)

        # Act
        stats = tracker.load_trade_history(trades)

        # Assert
        assert stats["trades_loaded"] == 3
        assert stats["win_rate"] == pytest.approx(66.67, abs=0.1)  # 2 out of 3

    @pytest.mark.asyncio
    async def test_skip_incomplete_trades(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test that incomplete trades are skipped."""
        # Arrange
        tracker = OrderTracker()
        now = datetime.now(UTC)

        # Complete trade
        complete_trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("50500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            status="CLOSED",
            opened_at=now,
            closed_at=now,
        )

        # Incomplete trade (missing exit_price)
        incomplete_trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=None,  # Missing!
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            status="CLOSED",
            opened_at=now,
            closed_at=now,
        )

        async_session.add(complete_trade)
        async_session.add(incomplete_trade)
        await async_session.commit()
        await async_session.refresh(complete_trade)
        await async_session.refresh(incomplete_trade)

        # Act
        stats = tracker.load_trade_history([complete_trade, incomplete_trade])

        # Assert - Only complete trade should be loaded
        assert stats["trades_loaded"] == 1
        assert tracker.total_trades == 1

    @pytest.mark.asyncio
    async def test_skip_trades_without_timestamps(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test that trades without timestamps are skipped."""
        # Arrange
        tracker = OrderTracker()
        now = datetime.now(UTC)

        # Complete trade
        complete_trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("50500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            status="CLOSED",
            opened_at=now,
            closed_at=now,
        )

        # Trade without closed_at
        no_timestamp_trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("50500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            status="CLOSED",
            opened_at=now,
            closed_at=None,  # Missing!
        )

        async_session.add(complete_trade)
        async_session.add(no_timestamp_trade)
        await async_session.commit()
        await async_session.refresh(complete_trade)
        await async_session.refresh(no_timestamp_trade)

        # Act
        stats = tracker.load_trade_history([complete_trade, no_timestamp_trade])

        # Assert - Only complete trade should be loaded
        assert stats["trades_loaded"] == 1
        assert tracker.total_trades == 1

    @pytest.mark.asyncio
    async def test_total_pnl_includes_history(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test that total_pnl includes loaded history."""
        # Arrange
        tracker = OrderTracker()
        tracker.set_initial_pnl(100.0)  # Initial PnL from exchange

        now = datetime.now(UTC)
        trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("50500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            status="CLOSED",
            opened_at=now,
            closed_at=now,
        )
        async_session.add(trade)
        await async_session.commit()
        await async_session.refresh(trade)

        # Act
        tracker.load_trade_history([trade])

        # Assert
        assert tracker.total_pnl == 100.5  # 100 initial + 0.5 from history

    @pytest.mark.asyncio
    async def test_date_range_calculation(
        self,
        async_session: AsyncSession,
        account: Account,
    ):
        """Test that date range is calculated correctly."""
        # Arrange
        tracker = OrderTracker()
        oldest_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        newest_date = datetime(2024, 1, 31, 23, 59, 59, tzinfo=UTC)

        trades = []
        for date in [oldest_date, newest_date]:
            trade = Trade(
                account_id=account.id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("50000.00"),
                exit_price=Decimal("50500.00"),
                quantity=Decimal("0.001"),
                pnl=Decimal("0.50"),
                status="CLOSED",
                opened_at=date,
                closed_at=date,
            )
            async_session.add(trade)
            trades.append(trade)

        await async_session.commit()
        for trade in trades:
            await async_session.refresh(trade)

        # Act
        stats = tracker.load_trade_history(trades)

        # Assert
        assert stats["date_range"] is not None
        # Compare dates without considering timezone for this test
        assert stats["date_range"][0].replace(tzinfo=UTC) == oldest_date
        assert stats["date_range"][1].replace(tzinfo=UTC) == newest_date

    @pytest.mark.asyncio
    async def test_integration_with_trade_repository(
        self,
        trade_repository: TradeRepository,
        account: Account,
    ):
        """Test full integration: save trades → load from repository."""
        # Arrange
        tracker = OrderTracker(account_id=account.id)
        now = datetime.now(UTC)

        # Save some trades via repository
        for _ in range(3):
            trade_data = {
                "account_id": account.id,
                "symbol": "BTC-USDT",
                "side": "LONG",
                "leverage": 10,
                "entry_price": Decimal("50000.00"),
                "exit_price": Decimal("50500.00"),
                "quantity": Decimal("0.001"),
                "pnl": Decimal("0.50"),
                "status": "CLOSED",
                "opened_at": now,
                "closed_at": now,
            }
            await trade_repository.save_trade(trade_data)

        # Act - Load back from repository
        trades = await trade_repository.get_trades_by_account(account.id, limit=100)
        closed_trades = [t for t in trades if t.status == "CLOSED"]
        stats = tracker.load_trade_history(closed_trades)

        # Assert
        assert stats["trades_loaded"] == 3
        assert tracker.total_trades == 3
        assert stats["win_rate"] == 100.0
