"""Tests for StrategyRepository."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.database.models import Account, User
from src.database.repositories import StrategyRepository


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
def second_account(session: Session, user: User) -> Account:
    """Create a second test account."""
    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Second Account",
        is_demo=False,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@pytest.fixture
def repository(session: Session) -> StrategyRepository:
    """Create StrategyRepository instance."""
    return StrategyRepository(session)


class TestStrategyRepository:
    """Test cases for StrategyRepository."""

    def test_create_strategy(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test creating a strategy from dict."""
        # Act
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "My Grid Strategy",
                "symbol": "BTC-USDT",
                "leverage": 10,
                "is_active": False,
            }
        )

        # Assert
        assert strategy.id is not None
        assert strategy.account_id == account.id
        assert strategy.name == "My Grid Strategy"
        assert strategy.symbol == "BTC-USDT"
        assert strategy.leverage == 10
        assert strategy.is_active is False
        assert strategy.created_at is not None
        assert strategy.updated_at is not None

    def test_create_strategy_with_defaults(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test creating a strategy uses model defaults."""
        # Act
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Default Strategy",
            }
        )

        # Assert
        assert strategy.symbol == "BTC-USDT"
        assert strategy.leverage == 10
        assert strategy.order_size_usdt == Decimal("100.00")
        assert strategy.margin_mode == "crossed"
        assert strategy.take_profit_percent == Decimal("0.50")
        assert strategy.is_active is False

    def test_get_by_account(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test getting all strategies for an account."""
        # Arrange
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Strategy 1",
            }
        )
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Strategy 2",
            }
        )

        # Act
        strategies = repository.get_by_account(account.id)

        # Assert
        assert len(strategies) == 2
        assert all(s.account_id == account.id for s in strategies)

    def test_get_by_account_empty(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test getting strategies for account with no strategies."""
        # Act
        strategies = repository.get_by_account(account.id)

        # Assert
        assert strategies == []

    def test_get_by_account_ordered_by_created_at(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test strategies are ordered by created_at desc."""
        # Arrange
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "First",
            }
        )
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Second",
            }
        )

        # Act
        strategies = repository.get_by_account(account.id)

        # Assert (most recent first)
        assert strategies[0].name == "Second"
        assert strategies[1].name == "First"

    def test_get_active_by_account(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test getting the active strategy for an account."""
        # Arrange
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Inactive Strategy",
                "is_active": False,
            }
        )
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Active Strategy",
                "is_active": True,
            }
        )

        # Act
        active = repository.get_active_by_account(account.id)

        # Assert
        assert active is not None
        assert active.name == "Active Strategy"
        assert active.is_active is True

    def test_get_active_by_account_none(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test getting active strategy when none is active."""
        # Arrange
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Inactive Strategy",
                "is_active": False,
            }
        )

        # Act
        active = repository.get_active_by_account(account.id)

        # Assert
        assert active is None

    def test_update_strategy(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test updating strategy fields."""
        # Arrange
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Original Name",
                "leverage": 10,
            }
        )

        # Act
        updated = repository.update_strategy(
            strategy.id,
            {
                "name": "Updated Name",
                "leverage": 20,
                "take_profit_percent": Decimal("0.75"),
            },
        )

        # Assert
        assert updated.name == "Updated Name"
        assert updated.leverage == 20
        assert updated.take_profit_percent == Decimal("0.75")

    def test_update_strategy_not_found(
        self,
        repository: StrategyRepository,
    ):
        """Test updating non-existent strategy raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found"):
            repository.update_strategy(uuid4(), {"name": "New Name"})

    def test_activate_strategy(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test activating a strategy."""
        # Arrange
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "To Activate",
                "is_active": False,
            }
        )

        # Act
        activated = repository.activate_strategy(strategy.id)

        # Assert
        assert activated.is_active is True

    def test_activate_strategy_deactivates_others(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test activating a strategy deactivates all others for same account."""
        # Arrange
        first = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "First Strategy",
                "is_active": True,
            }
        )
        second = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Second Strategy",
                "is_active": False,
            }
        )

        # Act
        repository.activate_strategy(second.id)

        # Assert - refetch to get updated values
        first_refreshed = repository.get_by_id(first.id)
        second_refreshed = repository.get_by_id(second.id)

        assert first_refreshed.is_active is False
        assert second_refreshed.is_active is True

    def test_activate_strategy_not_found(
        self,
        repository: StrategyRepository,
    ):
        """Test activating non-existent strategy raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found"):
            repository.activate_strategy(uuid4())

    def test_deactivate_all(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test deactivating all strategies for an account."""
        # Arrange - create strategies with one active (constraint allows only one active)
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Strategy 1",
                "is_active": True,
            }
        )
        repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Strategy 2",
                "is_active": False,
            }
        )

        # Act
        repository.deactivate_all(account.id)

        # Assert
        strategies = repository.get_by_account(account.id)
        assert len(strategies) == 2
        assert all(s.is_active is False for s in strategies)

    def test_deactivate_all_no_strategies(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test deactivating all when no strategies exist doesn't error."""
        # Act (should not raise)
        repository.deactivate_all(account.id)

        # Assert
        strategies = repository.get_by_account(account.id)
        assert strategies == []

    def test_activate_strategy_different_accounts(
        self,
        repository: StrategyRepository,
        account: Account,
        second_account: Account,
    ):
        """Test activating strategy doesn't affect other accounts."""
        # Arrange
        first_acc_strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "First Account Strategy",
                "is_active": True,
            }
        )
        second_acc_strategy = repository.create_strategy(
            {
                "account_id": second_account.id,
                "name": "Second Account Strategy",
                "is_active": False,
            }
        )

        # Act - activate strategy in second account
        repository.activate_strategy(second_acc_strategy.id)

        # Assert - first account's strategy should remain active
        first_refreshed = repository.get_by_id(first_acc_strategy.id)
        second_refreshed = repository.get_by_id(second_acc_strategy.id)

        assert first_refreshed.is_active is True
        assert second_refreshed.is_active is True

    def test_get_by_id(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test getting strategy by ID."""
        # Arrange
        created = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Test Strategy",
            }
        )

        # Act
        strategy = repository.get_by_id(created.id)

        # Assert
        assert strategy is not None
        assert strategy.id == created.id
        assert strategy.name == "Test Strategy"

    def test_get_by_id_not_found(
        self,
        repository: StrategyRepository,
    ):
        """Test getting non-existent strategy returns None."""
        # Act
        strategy = repository.get_by_id(uuid4())

        # Assert
        assert strategy is None

    def test_delete(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test deleting a strategy."""
        # Arrange
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "To Delete",
            }
        )

        # Act
        result = repository.delete(strategy.id)

        # Assert
        assert result is True
        deleted = repository.get_by_id(strategy.id)
        assert deleted is None

    def test_delete_not_found(
        self,
        repository: StrategyRepository,
    ):
        """Test deleting non-existent strategy returns False."""
        # Act
        result = repository.delete(uuid4())

        # Assert
        assert result is False

    def test_exists(
        self,
        repository: StrategyRepository,
        account: Account,
    ):
        """Test checking if strategy exists."""
        # Arrange
        strategy = repository.create_strategy(
            {
                "account_id": account.id,
                "name": "Existing",
            }
        )

        # Act
        exists = repository.exists(strategy.id)
        not_exists = repository.exists(uuid4())

        # Assert
        assert exists is True
        assert not_exists is False
