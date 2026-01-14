"""Tests for AccountRepository."""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.database.models import User
from src.database.repositories import AccountRepository


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
def repository(session: Session) -> AccountRepository:
    """Create AccountRepository instance."""
    return AccountRepository(session)


class TestAccountRepository:
    """Test cases for AccountRepository."""

    def test_create_account(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test creating an account."""
        # Act
        account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="My BingX Demo",
            is_demo=True,
            api_key_hash="abc123hash",  # pragma: allowlist secret
        )

        # Assert
        assert account.id is not None
        assert account.user_id == user.id
        assert account.exchange == "bingx"
        assert account.name == "My BingX Demo"
        assert account.is_demo is True
        assert account.api_key_hash == "abc123hash"  # pragma: allowlist secret
        assert account.created_at is not None
        assert account.updated_at is not None

    def test_create_account_without_api_key_hash(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test creating an account without API key hash."""
        # Act
        account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="My BingX Demo",
            is_demo=True,
        )

        # Assert
        assert account.api_key_hash is None

    def test_unique_constraint(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test unique constraint on user_id, exchange, name, is_demo."""
        # Arrange
        repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="My BingX",
            is_demo=True,
        )

        # Act & Assert
        with pytest.raises(Exception, match="UNIQUE constraint failed"):
            repository.create_account(
                user_id=user.id,
                exchange="bingx",
                name="My BingX",
                is_demo=True,
            )

    def test_same_name_different_mode_allowed(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test that same name is allowed for demo and live modes."""
        # Arrange & Act
        demo_account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="My BingX",
            is_demo=True,
        )

        live_account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="My BingX",
            is_demo=False,
        )

        # Assert
        assert demo_account.id != live_account.id
        assert demo_account.is_demo is True
        assert live_account.is_demo is False

    def test_get_by_id(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test getting account by ID."""
        # Arrange
        created = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="Test Account",
            is_demo=True,
        )

        # Act
        account = repository.get_by_id(created.id)

        # Assert
        assert account is not None
        assert account.id == created.id
        assert account.exchange == "bingx"

    def test_get_by_id_not_found(
        self,
        repository: AccountRepository,
    ):
        """Test getting non-existent account returns None."""
        # Act
        account = repository.get_by_id(uuid4())

        # Assert
        assert account is None

    def test_get_by_user(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test getting all accounts for a user."""
        # Arrange
        repository.create_account(user_id=user.id, exchange="bingx", name="Account 1", is_demo=True)
        repository.create_account(
            user_id=user.id, exchange="bingx", name="Account 2", is_demo=False
        )
        repository.create_account(
            user_id=user.id, exchange="binance", name="Account 3", is_demo=True
        )

        # Act
        accounts = repository.get_by_user(user.id)

        # Assert
        assert len(accounts) == 3

    def test_get_by_user_and_exchange(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test getting accounts filtered by exchange."""
        # Arrange
        repository.create_account(user_id=user.id, exchange="bingx", name="BingX 1", is_demo=True)
        repository.create_account(user_id=user.id, exchange="bingx", name="BingX 2", is_demo=False)
        repository.create_account(
            user_id=user.id, exchange="binance", name="Binance 1", is_demo=True
        )

        # Act
        bingx_accounts = repository.get_by_user_and_exchange(user.id, "bingx")

        # Assert
        assert len(bingx_accounts) == 2
        assert all(acc.exchange == "bingx" for acc in bingx_accounts)

    def test_get_by_user_and_exchange_with_demo_filter(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test getting accounts filtered by exchange and demo mode."""
        # Arrange
        repository.create_account(
            user_id=user.id, exchange="bingx", name="BingX Demo", is_demo=True
        )
        repository.create_account(
            user_id=user.id, exchange="bingx", name="BingX Live", is_demo=False
        )

        # Act
        demo_accounts = repository.get_by_user_and_exchange(user.id, "bingx", is_demo=True)

        # Assert
        assert len(demo_accounts) == 1
        assert demo_accounts[0].is_demo is True

    def test_update(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test updating account fields."""
        # Arrange
        account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="Old Name",
            is_demo=True,
        )

        # Act
        account.name = "New Name"
        account.api_key_hash = "newhash123"  # pragma: allowlist secret
        updated = repository.update(account)

        # Assert
        assert updated is not None
        assert updated.id == account.id
        assert updated.name == "New Name"
        assert updated.api_key_hash == "newhash123"  # pragma: allowlist secret

    def test_delete(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test deleting an account."""
        # Arrange
        account = repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="To Delete",
            is_demo=True,
        )

        # Act
        result = repository.delete(account.id)

        # Assert
        assert result is True
        deleted = repository.get_by_id(account.id)
        assert deleted is None

    def test_delete_not_found(
        self,
        repository: AccountRepository,
    ):
        """Test deleting non-existent account returns False."""
        # Act
        result = repository.delete(uuid4())

        # Assert
        assert result is False

    def test_exists(
        self,
        repository: AccountRepository,
        user: User,
    ):
        """Test checking if account exists."""
        # Arrange
        repository.create_account(
            user_id=user.id,
            exchange="bingx",
            name="Existing",
            is_demo=True,
        )

        # Act
        exists = repository.account_exists(user.id, "bingx", "Existing", True)
        not_exists = repository.account_exists(user.id, "bingx", "Non-Existent", True)

        # Assert
        assert exists is True
        assert not_exists is False
