"""Account service for business logic layer."""

import hashlib
from uuid import UUID

from config import BingXConfig
from src.client.bingx_client import BingXClient
from src.database.models.account import Account
from src.database.repositories.account_repository import AccountRepository


class AccountService:
    """Service layer for account management.

    Provides high-level business logic for managing trading accounts,
    including API credential validation and account lifecycle operations.
    """

    def __init__(self, repository: AccountRepository):
        """Initialize service with repository.

        Args:
            repository: AccountRepository instance.
        """
        self.repository = repository

    async def add_account(
        self,
        user_id: UUID,
        exchange: str,
        name: str,
        api_key: str,
        api_secret: str,
        is_demo: bool = True,
    ) -> Account:
        """Add a new trading account for a user.

        Args:
            user_id: User ID who owns this account.
            exchange: Exchange name (e.g., 'bingx', 'binance', 'bybit').
            name: User-friendly account name.
            api_key: API key from the exchange.
            api_secret: API secret from the exchange.
            is_demo: True for demo mode, False for live mode.

        Returns:
            Created Account instance.

        Raises:
            ValueError: If account with same parameters already exists.
            ConnectionError: If API credentials are invalid.
        """
        # Check if account already exists
        if self.repository.account_exists(user_id, exchange, name, is_demo):
            msg = f"Account already exists: {exchange}/{name} (demo={is_demo})"
            raise ValueError(msg)

        # Validate API credentials
        if not self.validate_api_credentials(exchange, api_key, api_secret, is_demo):
            raise ConnectionError("Invalid API credentials or unable to connect to exchange")

        # Create account with hashed API key
        api_key_hash = self.hash_api_key(api_key)
        return self.repository.create_account(
            user_id=user_id,
            exchange=exchange,
            name=name,
            is_demo=is_demo,
            api_key_hash=api_key_hash,
        )

    async def validate_api_credentials(
        self,
        exchange: str,
        api_key: str,
        api_secret: str,
        is_demo: bool,
    ) -> bool:
        """Validate API credentials by testing connection to exchange.

        Args:
            exchange: Exchange name.
            api_key: API key to test.
            api_secret: API secret to test.
            is_demo: True for demo mode, False for live mode.

        Returns:
            True if credentials are valid and connection succeeds.
        """
        if exchange.lower() == "bingx":
            return self._validate_bingx_credentials(api_key, api_secret, is_demo)

        # Add support for other exchanges here
        # elif exchange.lower() == "binance":
        #     return self._validate_binance_credentials(api_key, api_secret, is_demo)

        msg = f"Unsupported exchange: {exchange}"
        raise ValueError(msg)

    async def _validate_bingx_credentials(
        self,
        api_key: str,
        api_secret: str,
        is_demo: bool,
    ) -> bool:
        """Validate BingX API credentials.

        Args:
            api_key: BingX API key.
            api_secret: BingX API secret.
            is_demo: True for demo mode, False for live mode.

        Returns:
            True if credentials are valid.
        """
        try:
            # Create BingXConfig with provided credentials
            config = BingXConfig(api_key=api_key, secret_key=api_secret, is_demo=is_demo)
            client = BingXClient(config)

            # Test connection by fetching account balance
            balance = client.get_balance()
            return balance is not None

        except Exception:  # noqa: BLE001
            return False

    async def get_user_accounts(self, user_id: UUID) -> list[Account]:
        """Get all accounts for a user.

        Args:
            user_id: User UUID.

        Returns:
            List of Account instances.
        """
        return self.repository.get_by_user(user_id)

    async def get_active_account(self, user_id: UUID, exchange: str) -> Account | None:
        """Get the first active account for a user and exchange.

        Args:
            user_id: User UUID.
            exchange: Exchange name.

        Returns:
            Account instance or None if not found.

        Note:
            Returns the first account found. For multi-account selection,
            use get_user_accounts() and implement custom selection logic.
        """
        accounts = self.repository.get_by_user_and_exchange(user_id, exchange)
        return accounts[0] if accounts else None

    def hash_api_key(self, api_key: str) -> str:
        """Generate SHA-256 hash of API key.

        Args:
            api_key: API key to hash.

        Returns:
            Hex-encoded SHA-256 hash.

        Note:
            This is used for uniqueness identification only,
            not for cryptographic security of the key itself.
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
