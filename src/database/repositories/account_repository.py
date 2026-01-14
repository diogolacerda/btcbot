"""Account repository for managing trading accounts."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.account import Account
from src.database.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository[Account]):
    """Repository for Account CRUD operations.

    Provides async methods for creating, reading, updating, and deleting
    trading accounts across multiple exchanges and modes (demo/live).

    Inherits generic CRUD operations from BaseRepository:
    - get_by_id(account_id: UUID) -> Account | None
    - get_all(skip: int, limit: int) -> list[Account]
    - create(account: Account) -> Account
    - update(account: Account) -> Account
    - delete(account_id: UUID) -> bool
    - exists(account_id: UUID) -> bool
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, Account)

    def create_account(
        self,
        user_id: UUID,
        exchange: str,
        name: str,
        is_demo: bool,
        api_key_hash: str | None = None,
    ) -> Account:
        """Create a new account.

        Args:
            user_id: User ID who owns this account.
            exchange: Exchange name (e.g., 'bingx', 'binance', 'bybit').
            name: User-friendly account name.
            is_demo: True for demo mode, False for live mode.
            api_key_hash: Optional SHA-256 hash of API key for unique identification.

        Returns:
            Created Account instance.

        Raises:
            IntegrityError: If account with same user_id, exchange, name, and is_demo already exists.
        """
        account = Account(
            user_id=user_id,
            exchange=exchange,
            name=name,
            is_demo=is_demo,
            api_key_hash=api_key_hash,
        )
        return self.create(account)

    def get_by_user(self, user_id: UUID) -> list[Account]:
        """Get all accounts for a user.

        Args:
            user_id: User UUID.

        Returns:
            List of Account instances.
        """
        result = self.session.execute(select(Account).where(Account.user_id == user_id))
        return list(result.scalars().all())

    def get_by_user_and_exchange(
        self,
        user_id: UUID,
        exchange: str,
        is_demo: bool | None = None,
    ) -> list[Account]:
        """Get accounts filtered by user, exchange, and optionally demo mode.

        Args:
            user_id: User UUID.
            exchange: Exchange name.
            is_demo: Optional filter for demo mode. If None, returns both demo and live.

        Returns:
            List of Account instances matching the criteria.
        """
        query = select(Account).where(Account.user_id == user_id, Account.exchange == exchange)

        if is_demo is not None:
            query = query.where(Account.is_demo == is_demo)

        result = self.session.execute(query)
        return list(result.scalars().all())

    def account_exists(
        self,
        user_id: UUID,
        exchange: str,
        name: str,
        is_demo: bool,
    ) -> bool:
        """Check if account already exists with specific parameters.

        Args:
            user_id: User UUID.
            exchange: Exchange name.
            name: Account name.
            is_demo: Demo mode flag.

        Returns:
            True if account exists with these exact parameters.
        """
        result = self.session.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.exchange == exchange,
                Account.name == name,
                Account.is_demo == is_demo,
            )
        )
        return result.scalar_one_or_none() is not None
