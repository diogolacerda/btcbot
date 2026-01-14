"""Repository for Strategy CRUD operations.

Provides async methods for managing trading strategies, with special handling
for active strategy management (only one active strategy per account).
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.database.models.strategy import Strategy
from src.database.repositories.base_repository import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for Strategy CRUD operations.

    Provides async methods for creating, reading, updating, and deleting
    trading strategies. Ensures only one strategy is active per account.

    Inherits generic CRUD operations from BaseRepository:
    - get_by_id(strategy_id: UUID) -> Strategy | None
    - get_all(skip: int, limit: int) -> list[Strategy]
    - create(strategy: Strategy) -> Strategy
    - update(strategy: Strategy) -> Strategy
    - delete(strategy_id: UUID) -> bool
    - exists(strategy_id: UUID) -> bool

    Custom methods:
    - get_by_account(account_id) -> list[Strategy]
    - get_active_by_account(account_id) -> Strategy | None
    - create_strategy(strategy_data: dict) -> Strategy
    - update_strategy(strategy_id: UUID, updates: dict) -> Strategy
    - activate_strategy(strategy_id: UUID) -> Strategy
    - deactivate_all(account_id: UUID) -> None
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, Strategy)

    def get_by_account(self, account_id: UUID) -> list[Strategy]:
        """Get all strategies for a specific account.

        Args:
            account_id: UUID of the account.

        Returns:
            List of Strategy instances for the account.

        Raises:
            Exception: If database operation fails.
        """
        try:
            result = self.session.execute(
                select(Strategy)
                .where(Strategy.account_id == account_id)
                .order_by(Strategy.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Error fetching strategies for account {account_id}: {e}") from e

    def get_active_by_account(self, account_id: UUID) -> Strategy | None:
        """Get the active strategy for a specific account.

        Each account can have at most one active strategy at a time.

        Args:
            account_id: UUID of the account.

        Returns:
            Active Strategy instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.
        """
        try:
            result = self.session.execute(
                select(Strategy).where(
                    Strategy.account_id == account_id,
                    Strategy.is_active == True,  # noqa: E712
                )
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            raise Exception(f"Error fetching active strategy for account {account_id}: {e}") from e

    def create_strategy(self, strategy_data: dict) -> Strategy:
        """Create a new strategy from a dictionary.

        Args:
            strategy_data: Dictionary containing strategy fields.
                Required: account_id, name
                Optional: All other Strategy model fields

        Returns:
            Created Strategy instance.

        Raises:
            KeyError: If required fields are missing.
            Exception: If database operation fails.

        Example:
            strategy = repo.create_strategy({
                "account_id": account_id,
                "name": "My Grid Strategy",
                "symbol": "BTC-USDT",
                "leverage": 10,
                "is_active": True,
            })
        """
        try:
            strategy = Strategy(**strategy_data)
            return self.create(strategy)
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error creating strategy: {e}") from e

    def update_strategy(self, strategy_id: UUID, updates: dict) -> Strategy:
        """Update specific fields of a strategy.

        Args:
            strategy_id: UUID of the strategy to update.
            updates: Dictionary of field-value pairs to update.

        Returns:
            Updated Strategy instance.

        Raises:
            ValueError: If strategy not found.
            Exception: If database operation fails.

        Example:
            strategy = repo.update_strategy(
                strategy_id,
                {"leverage": 20, "take_profit_percent": Decimal("0.8")}
            )
        """
        try:
            strategy = self.get_by_id(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            for field, value in updates.items():
                if hasattr(strategy, field):
                    setattr(strategy, field, value)

            return self.update(strategy)
        except ValueError:
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error updating strategy {strategy_id}: {e}") from e

    def activate_strategy(self, strategy_id: UUID) -> Strategy:
        """Activate a strategy, deactivating all others for the same account.

        This ensures only one strategy is active per account at any time.

        Args:
            strategy_id: UUID of the strategy to activate.

        Returns:
            Activated Strategy instance.

        Raises:
            ValueError: If strategy not found.
            Exception: If database operation fails.

        Example:
            activated = repo.activate_strategy(strategy_id)
            print(f"Strategy '{activated.name}' is now active")
        """
        try:
            strategy = self.get_by_id(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            # Deactivate all other strategies for this account
            self.deactivate_all(strategy.account_id)

            # Activate the target strategy
            strategy.is_active = True
            return self.update(strategy)
        except ValueError:
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error activating strategy {strategy_id}: {e}") from e

    def deactivate_all(self, account_id: UUID) -> None:
        """Deactivate all strategies for an account.

        Args:
            account_id: UUID of the account.

        Raises:
            Exception: If database operation fails.

        Example:
            repo.deactivate_all(account_id)
        """
        try:
            self.session.execute(
                update(Strategy).where(Strategy.account_id == account_id).values(is_active=False)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error deactivating strategies for account {account_id}: {e}") from e
