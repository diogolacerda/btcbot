"""Tests for AccountService."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.database.repositories import AccountRepository
from src.services import AccountService


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
async def repository(async_session: AsyncSession) -> AccountRepository:
    """Create AccountRepository instance."""
    return AccountRepository(async_session)


@pytest.fixture
async def service(repository: AccountRepository) -> AccountService:
    """Create AccountService instance."""
    return AccountService(repository)


class TestAccountService:
    """Test cases for AccountService."""

    @pytest.mark.asyncio
    async def test_add_account_success(
        self,
        service: AccountService,
        user: User,
    ):
        """Test adding a new account with valid credentials."""
        # Arrange
        with patch.object(service, "validate_api_credentials", return_value=True):
            # Act
            account = await service.add_account(
                user_id=user.id,
                exchange="bingx",
                name="My BingX",
                api_key="test_key",  # pragma: allowlist secret
                api_secret="test_secret",  # pragma: allowlist secret
                is_demo=True,
            )

            # Assert
            assert account.user_id == user.id
            assert account.exchange == "bingx"
            assert account.name == "My BingX"
            assert account.is_demo is True
            assert account.api_key_hash is not None

    @pytest.mark.asyncio
    async def test_add_account_invalid_credentials(
        self,
        service: AccountService,
        user: User,
    ):
        """Test adding account with invalid API credentials."""
        # Arrange
        with patch.object(service, "validate_api_credentials", return_value=False):
            # Act & Assert
            with pytest.raises(ConnectionError, match="Invalid API credentials"):
                await service.add_account(
                    user_id=user.id,
                    exchange="bingx",
                    name="My BingX",
                    api_key="invalid_key",  # pragma: allowlist secret
                    api_secret="invalid_secret",  # pragma: allowlist secret
                    is_demo=True,
                )

    @pytest.mark.asyncio
    async def test_add_account_duplicate(
        self,
        service: AccountService,
        user: User,
    ):
        """Test adding duplicate account raises ValueError."""
        # Arrange
        with patch.object(service, "validate_api_credentials", return_value=True):
            await service.add_account(
                user_id=user.id,
                exchange="bingx",
                name="Duplicate",
                api_key="key1",  # pragma: allowlist secret
                api_secret="secret1",  # pragma: allowlist secret
                is_demo=True,
            )

            # Act & Assert
            with pytest.raises(ValueError, match="Account already exists"):
                await service.add_account(
                    user_id=user.id,
                    exchange="bingx",
                    name="Duplicate",
                    api_key="key2",  # pragma: allowlist secret
                    api_secret="secret2",  # pragma: allowlist secret
                    is_demo=True,
                )

    @pytest.mark.asyncio
    async def test_validate_bingx_credentials_success(
        self,
        service: AccountService,
    ):
        """Test validating BingX credentials successfully."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_balance.return_value = {"balance": "1000"}

        with patch("src.services.account_service.BingXClient", return_value=mock_client):
            # Act
            is_valid = await service._validate_bingx_credentials(
                api_key="valid_key",  # pragma: allowlist secret
                api_secret="valid_secret",  # pragma: allowlist secret
                is_demo=True,
            )

            # Assert
            assert is_valid is True
            mock_client.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_bingx_credentials_failure(
        self,
        service: AccountService,
    ):
        """Test validating BingX credentials with API error."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_balance.side_effect = Exception("API Error")

        with patch("src.services.account_service.BingXClient", return_value=mock_client):
            # Act
            is_valid = await service._validate_bingx_credentials(
                api_key="invalid_key",  # pragma: allowlist secret
                api_secret="invalid_secret",  # pragma: allowlist secret
                is_demo=True,
            )

            # Assert
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_api_credentials_bingx(
        self,
        service: AccountService,
    ):
        """Test validate_api_credentials routes to BingX validator."""
        # Arrange
        with patch.object(
            service, "_validate_bingx_credentials", return_value=True
        ) as mock_validate:
            # Act
            is_valid = await service.validate_api_credentials(
                exchange="bingx",
                api_key="key",  # pragma: allowlist secret
                api_secret="secret",  # pragma: allowlist secret
                is_demo=True,
            )

            # Assert
            assert is_valid is True
            mock_validate.assert_called_once_with("key", "secret", True)

    @pytest.mark.asyncio
    async def test_validate_api_credentials_unsupported_exchange(
        self,
        service: AccountService,
    ):
        """Test validate_api_credentials with unsupported exchange."""
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported exchange"):
            await service.validate_api_credentials(
                exchange="unsupported",
                api_key="key",  # pragma: allowlist secret
                api_secret="secret",  # pragma: allowlist secret
                is_demo=True,
            )

    @pytest.mark.asyncio
    async def test_get_user_accounts(
        self,
        service: AccountService,
        user: User,
    ):
        """Test getting all accounts for a user."""
        # Arrange
        with patch.object(service, "validate_api_credentials", return_value=True):
            await service.add_account(
                user_id=user.id,
                exchange="bingx",
                name="Account 1",
                api_key="key1",  # pragma: allowlist secret
                api_secret="secret1",  # pragma: allowlist secret
                is_demo=True,
            )
            await service.add_account(
                user_id=user.id,
                exchange="binance",
                name="Account 2",
                api_key="key2",  # pragma: allowlist secret
                api_secret="secret2",  # pragma: allowlist secret
                is_demo=False,
            )

        # Act
        accounts = await service.get_user_accounts(user.id)

        # Assert
        assert len(accounts) == 2

    @pytest.mark.asyncio
    async def test_get_active_account(
        self,
        service: AccountService,
        user: User,
    ):
        """Test getting active account for user and exchange."""
        # Arrange
        with patch.object(service, "validate_api_credentials", return_value=True):
            created = await service.add_account(
                user_id=user.id,
                exchange="bingx",
                name="My BingX",
                api_key="key",  # pragma: allowlist secret
                api_secret="secret",  # pragma: allowlist secret
                is_demo=True,
            )

        # Act
        account = await service.get_active_account(user.id, "bingx")

        # Assert
        assert account is not None
        assert account.id == created.id

    @pytest.mark.asyncio
    async def test_get_active_account_not_found(
        self,
        service: AccountService,
        user: User,
    ):
        """Test getting active account returns None when not found."""
        # Act
        account = await service.get_active_account(user.id, "nonexistent")

        # Assert
        assert account is None

    def test_hash_api_key(self, service: AccountService):
        """Test API key hashing."""
        # Arrange
        api_key = "my_secret_api_key"  # pragma: allowlist secret

        # Act
        hash1 = service.hash_api_key(api_key)
        hash2 = service.hash_api_key(api_key)

        # Assert
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        assert hash1 == hash2  # Same input produces same hash
        assert hash1 != api_key  # Hash is different from original

    def test_hash_api_key_different_inputs(self, service: AccountService):
        """Test that different API keys produce different hashes."""
        # Act
        hash1 = service.hash_api_key("key1")
        hash2 = service.hash_api_key("key2")

        # Assert
        assert hash1 != hash2
