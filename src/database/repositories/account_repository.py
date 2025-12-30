"""Account repository for managing trading accounts."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.account import Account


class AccountRepository:
    """Repository for Account CRUD operations.

    Provides async methods for creating, reading, updating, and deleting
    trading accounts across multiple exchanges and modes (demo/live).
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        self.session = session

    async def create(
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
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """Get account by ID.

        Args:
            account_id: Account UUID.

        Returns:
            Account instance or None if not found.
        """
        result = await self.session.execute(select(Account).where(Account.id == account_id))
        account: Account | None = result.scalar_one_or_none()
        return account

    async def get_by_user(self, user_id: UUID) -> list[Account]:
        """Get all accounts for a user.

        Args:
            user_id: User UUID.

        Returns:
            List of Account instances.
        """
        result = await self.session.execute(select(Account).where(Account.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_user_and_exchange(
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

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, account_id: UUID, **kwargs: str) -> Account | None:
        """Update account fields.

        Args:
            account_id: Account UUID.
            **kwargs: Fields to update (name, api_key_hash, etc.).

        Returns:
            Updated Account instance or None if not found.

        Example:
            await repo.update(account_id, name="New Name", api_key_hash="abc123")
        """
        account = await self.get_by_id(account_id)
        if not account:
            return None

        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)

        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def delete(self, account_id: UUID) -> bool:
        """Delete account by ID.

        Args:
            account_id: Account UUID.

        Returns:
            True if account was deleted, False if not found.
        """
        account = await self.get_by_id(account_id)
        if not account:
            return False

        await self.session.delete(account)
        await self.session.commit()
        return True

    async def exists(
        self,
        user_id: UUID,
        exchange: str,
        name: str,
        is_demo: bool,
    ) -> bool:
        """Check if account already exists.

        Args:
            user_id: User UUID.
            exchange: Exchange name.
            name: Account name.
            is_demo: Demo mode flag.

        Returns:
            True if account exists with these exact parameters.
        """
        result = await self.session.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.exchange == exchange,
                Account.name == name,
                Account.is_demo == is_demo,
            )
        )
        return result.scalar_one_or_none() is not None
