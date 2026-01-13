"""Tests for TradeRepository."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.database.models import Account, Trade, User
from src.database.repositories import TradeRepository


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",  # pragma: allowlist secret
        name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def account(session: Session, user: User) -> Account:
    """Create a test account."""
    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@pytest.fixture
def repository(session: Session) -> TradeRepository:
    """Create TradeRepository instance."""
    return TradeRepository(session)


class TestTradeRepository:
    """Test cases for TradeRepository."""

    def test_save_trade(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test saving a new trade."""
        # Arrange
        trade_data = {
            "account_id": account.id,
            "exchange_order_id": "12345",
            "exchange_tp_order_id": "12346",
            "symbol": "BTC-USDT",
            "side": "LONG",
            "leverage": 10,
            "entry_price": Decimal("50000.00"),
            "quantity": Decimal("0.1"),
            "tp_price": Decimal("50500.00"),
            "tp_percent": Decimal("1.0"),
            "trading_fee": Decimal("5.0"),
            "funding_fee": Decimal("0.5"),
            "status": "OPEN",
            "grid_level": 5,
            "opened_at": datetime.now(UTC),
            "filled_at": datetime.now(UTC),
        }

        # Act
        trade_id = repository.save_trade(trade_data)

        # Assert
        assert trade_id is not None
        trade = repository.get_by_id(trade_id)
        assert trade is not None
        assert trade.account_id == account.id
        assert trade.exchange_order_id == "12345"
        assert trade.entry_price == Decimal("50000.00")
        assert trade.status == "OPEN"

    def test_save_trade_minimal_data(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test saving trade with minimal required data."""
        # Arrange
        trade_data = {
            "account_id": account.id,
            "entry_price": Decimal("50000.00"),
            "quantity": Decimal("0.1"),
        }

        # Act
        trade_id = repository.save_trade(trade_data)

        # Assert
        trade = repository.get_by_id(trade_id)
        assert trade is not None
        assert trade.symbol == "BTC-USDT"  # default
        assert trade.side == "LONG"  # default
        assert trade.leverage == 10  # default
        assert trade.status == "OPEN"  # default
        assert trade.trading_fee == Decimal("0")  # default
        assert trade.funding_fee == Decimal("0")  # default

    def test_get_trades_by_account(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting trades for an account."""
        # Arrange - create 3 trades
        for _ in range(3):
            repository.save_trade(
                {
                    "account_id": account.id,
                    "entry_price": Decimal("50000.00"),
                    "quantity": Decimal("0.1"),
                }
            )

        # Act
        trades = repository.get_trades_by_account(account.id)

        # Assert
        assert len(trades) == 3
        assert all(t.account_id == account.id for t in trades)

    def test_get_trades_by_account_with_pagination(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test pagination when getting trades."""
        # Arrange - create 5 trades
        for _ in range(5):
            repository.save_trade(
                {
                    "account_id": account.id,
                    "entry_price": Decimal("50000.00"),
                    "quantity": Decimal("0.1"),
                }
            )

        # Act
        first_page = repository.get_trades_by_account(account.id, limit=2, offset=0)
        second_page = repository.get_trades_by_account(account.id, limit=2, offset=2)

        # Assert
        assert len(first_page) == 2
        assert len(second_page) == 2
        assert first_page[0].id != second_page[0].id

    def test_get_trades_by_period(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting trades within a time period."""
        # Arrange
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # Create trades at different times
        repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("50000.00"),
                "quantity": Decimal("0.1"),
                "opened_at": two_days_ago,
            }
        )
        repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("51000.00"),
                "quantity": Decimal("0.1"),
                "opened_at": yesterday,
            }
        )
        repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("52000.00"),
                "quantity": Decimal("0.1"),
                "opened_at": now,
            }
        )

        # Act - get trades from yesterday onwards
        trades = repository.get_trades_by_period(
            account.id,
            start=yesterday - timedelta(hours=1),
            end=now + timedelta(hours=1),
        )

        # Assert
        assert len(trades) == 2
        # Check timestamps with timezone awareness
        start_check = yesterday - timedelta(hours=1)
        for t in trades:
            # Make datetime timezone-aware if it's naive (SQLite returns naive datetimes)
            opened_at = t.opened_at if t.opened_at.tzinfo else t.opened_at.replace(tzinfo=UTC)
            assert opened_at >= start_check

    def test_get_open_trades(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting only open trades."""
        # Arrange
        # Create 2 open trades
        repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("50000.00"),
                "quantity": Decimal("0.1"),
                "status": "OPEN",
            }
        )
        repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("51000.00"),
                "quantity": Decimal("0.1"),
                "status": "OPEN",
            }
        )

        # Create 1 closed trade
        trade_id_3 = repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("52000.00"),
                "quantity": Decimal("0.1"),
                "status": "CLOSED",
            }
        )

        # Close one of the open trades
        repository.update_trade_exit(
            trade_id_3,
            exit_price=Decimal("52500.00"),
            pnl=Decimal("50.00"),
        )

        # Act
        open_trades = repository.get_open_trades(account.id)

        # Assert
        assert len(open_trades) == 2
        assert all(t.status == "OPEN" for t in open_trades)

    def test_update_trade_exit(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test updating trade exit information."""
        # Arrange
        trade_id = repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("50000.00"),
                "quantity": Decimal("0.1"),
                "status": "OPEN",
            }
        )

        # Act
        repository.update_trade_exit(
            trade_id,
            exit_price=Decimal("50500.00"),
            pnl=Decimal("50.00"),
            pnl_percent=Decimal("1.0"),
        )

        # Assert
        trade = repository.get_by_id(trade_id)
        assert trade is not None
        assert trade.exit_price == Decimal("50500.00")
        assert trade.pnl == Decimal("50.00")
        assert trade.pnl_percent == Decimal("1.0")
        assert trade.status == "CLOSED"
        assert trade.closed_at is not None

    def test_update_trade_exit_not_found(
        self,
        repository: TradeRepository,
    ):
        """Test updating non-existent trade raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Trade .* not found"):
            repository.update_trade_exit(
                uuid4(),
                exit_price=Decimal("50500.00"),
                pnl=Decimal("50.00"),
            )

    def test_get_by_id(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting trade by ID."""
        # Arrange
        trade_id = repository.save_trade(
            {
                "account_id": account.id,
                "entry_price": Decimal("50000.00"),
                "quantity": Decimal("0.1"),
            }
        )

        # Act
        trade = repository.get_by_id(trade_id)

        # Assert
        assert trade is not None
        assert trade.id == trade_id
        assert trade.account_id == account.id

    def test_get_by_id_not_found(
        self,
        repository: TradeRepository,
    ):
        """Test getting non-existent trade returns None."""
        # Act
        trade = repository.get_by_id(uuid4())

        # Assert
        assert trade is None

    def test_get_by_exchange_order_id(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting trade by exchange order ID."""
        # Arrange
        repository.save_trade(
            {
                "account_id": account.id,
                "exchange_order_id": "ORDER-12345",
                "entry_price": Decimal("50000.00"),
                "quantity": Decimal("0.1"),
            }
        )

        # Act
        trade = repository.get_by_exchange_order_id(account.id, "ORDER-12345")

        # Assert
        assert trade is not None
        assert trade.exchange_order_id == "ORDER-12345"
        assert trade.account_id == account.id

    def test_get_by_exchange_order_id_not_found(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test getting non-existent exchange order returns None."""
        # Act
        trade = repository.get_by_exchange_order_id(account.id, "NON-EXISTENT")

        # Assert
        assert trade is None

    def test_trades_ordered_by_created_at_desc(
        self,
        repository: TradeRepository,
        account: Account,
        session: Session,
    ):
        """Test that trades are ordered by created_at descending."""
        # Arrange - Create trades with explicit created_at timestamps

        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)

        trade_1 = Trade(
            account_id=account.id,
            entry_price=Decimal("50000.00"),
            quantity=Decimal("0.1"),
            created_at=yesterday,
        )
        trade_2 = Trade(
            account_id=account.id,
            entry_price=Decimal("51000.00"),
            quantity=Decimal("0.1"),
            created_at=now,
        )

        session.add(trade_1)
        session.add(trade_2)
        session.commit()
        session.refresh(trade_1)
        session.refresh(trade_2)

        # Act
        trades = repository.get_trades_by_account(account.id)

        # Assert
        assert len(trades) == 2
        # Most recent first (trade_2 created at 'now')
        assert trades[0].id == trade_2.id
        assert trades[1].id == trade_1.id
        # Verify ordering by created_at
        assert trades[0].created_at >= trades[1].created_at

    def test_save_trade_idempotent_duplicate_prevention(
        self,
        repository: TradeRepository,
        account: Account,
    ):
        """Test that saving a trade with duplicate exchange_order_id is idempotent."""
        # Arrange - Create trade data with exchange_order_id
        exchange_order_id = "TEST_ORDER_12345"
        trade_data = {
            "account_id": account.id,
            "exchange_order_id": exchange_order_id,
            "symbol": "BTC-USDT",
            "side": "LONG",
            "leverage": 10,
            "entry_price": Decimal("50000.00"),
            "quantity": Decimal("0.1"),
            "status": "OPEN",
        }

        # Act - Save the same trade twice (simulating race condition)
        first_id = repository.save_trade(trade_data)
        second_id = repository.save_trade(trade_data)

        # Assert - Both calls should return the same ID (idempotent)
        assert first_id == second_id

        # Verify only one trade was created
        trades = repository.get_trades_by_account(account.id)
        assert len(trades) == 1
        assert trades[0].exchange_order_id == exchange_order_id
