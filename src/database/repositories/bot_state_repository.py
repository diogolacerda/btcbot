"""Repository for BotState model operations."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.bot_state import BotState
from src.utils.logger import main_logger


class BotStateRepository:
    """Repository for managing BotState persistence.

    Provides methods to save and retrieve bot cycle state for accounts.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def get_by_account(self, account_id: UUID) -> BotState | None:
        """
        Get bot state for an account.

        Args:
            account_id: Account UUID

        Returns:
            BotState if found, None otherwise
        """
        try:
            stmt = select(BotState).where(BotState.account_id == account_id)
            result = await self.session.execute(stmt)
            bot_state = result.scalar_one_or_none()
            return bot_state if isinstance(bot_state, BotState) else None
        except Exception as e:
            main_logger.error(f"Error fetching bot state for account {account_id}: {e}")
            raise

    async def save_state(
        self,
        account_id: UUID,
        cycle_activated: bool,
        last_state: str,
        *,
        activated_at: datetime | None = None,
    ) -> BotState:
        """
        Save or update bot state for an account.

        Args:
            account_id: Account UUID
            cycle_activated: Whether cycle is activated
            last_state: Last GridState value
            activated_at: When cycle was activated (for new activations)

        Returns:
            Saved BotState instance
        """
        try:
            # Try to get existing state
            bot_state = await self.get_by_account(account_id)

            if bot_state:
                # Update existing state
                bot_state.cycle_activated = cycle_activated
                bot_state.last_state = last_state
                bot_state.last_state_change_at = datetime.now(UTC)

                # Update activated_at only if newly activated
                if cycle_activated and not bot_state.activated_at:
                    bot_state.activated_at = activated_at or datetime.now(UTC)

                # Clear activated_at if cycle is deactivated
                if not cycle_activated:
                    bot_state.activated_at = None

            else:
                # Create new state
                bot_state = BotState(
                    account_id=account_id,
                    cycle_activated=cycle_activated,
                    last_state=last_state,
                    activated_at=activated_at if cycle_activated else None,
                    last_state_change_at=datetime.now(UTC),
                )
                self.session.add(bot_state)

            await self.session.commit()
            await self.session.refresh(bot_state)
            return bot_state

        except Exception as e:
            await self.session.rollback()
            main_logger.error(f"Error saving bot state for account {account_id}: {e}")
            raise

    async def is_state_valid(
        self,
        bot_state: BotState,
        max_age_hours: int = 24,
    ) -> bool:
        """
        Check if bot state is still valid for restoration.

        Args:
            bot_state: BotState instance
            max_age_hours: Maximum age in hours for state to be valid

        Returns:
            True if state is valid and should be restored, False otherwise
        """
        if not bot_state.cycle_activated:
            return False

        if not bot_state.activated_at:
            # If cycle is activated but no activation timestamp, something is wrong
            main_logger.warning(f"Bot state {bot_state.id} is activated but has no activated_at")
            return False

        # Check if state is too old
        age = datetime.now(UTC) - bot_state.activated_at
        max_age = timedelta(hours=max_age_hours)

        if age > max_age:
            main_logger.info(
                f"Bot state is too old ({age.total_seconds() / 3600:.1f}h), "
                f"max age: {max_age_hours}h"
            )
            return False

        return True

    async def clear_state(self, account_id: UUID) -> None:
        """
        Clear bot state for an account (delete from database).

        Args:
            account_id: Account UUID
        """
        try:
            bot_state = await self.get_by_account(account_id)
            if bot_state:
                await self.session.delete(bot_state)
                await self.session.commit()
                main_logger.info(f"Cleared bot state for account {account_id}")
        except Exception as e:
            await self.session.rollback()
            main_logger.error(f"Error clearing bot state for account {account_id}: {e}")
            raise

    def to_dict(self, bot_state: BotState) -> dict[str, Any]:
        """
        Convert BotState to dictionary representation.

        Args:
            bot_state: BotState instance

        Returns:
            Dictionary with state data
        """
        return {
            "id": str(bot_state.id),
            "account_id": str(bot_state.account_id),
            "cycle_activated": bot_state.cycle_activated,
            "last_state": bot_state.last_state,
            "activated_at": bot_state.activated_at.isoformat() if bot_state.activated_at else None,
            "last_state_change_at": (
                bot_state.last_state_change_at.isoformat()
                if bot_state.last_state_change_at
                else None
            ),
            "created_at": bot_state.created_at.isoformat(),
            "updated_at": bot_state.updated_at.isoformat(),
        }
