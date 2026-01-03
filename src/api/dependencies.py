"""Shared dependencies for FastAPI endpoints.

This module provides dependency injection functions for:
- Database sessions
- Repositories
- BingX client
- GridManager instance
- Filter registry
- Authentication
- Global account ID (single-account mode)
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.database.repositories.trade_repository import TradeRepository
from src.filters.registry import FilterRegistry

# Global account ID for single-account mode
# Set during startup in main.py
_GLOBAL_ACCOUNT_ID: UUID | None = None


def set_global_account_id(account_id: UUID) -> None:
    """Set the global account ID (single-account mode).

    This is called during bot startup in main.py after account creation.

    Args:
        account_id: The UUID of the account to use globally.
    """
    global _GLOBAL_ACCOUNT_ID
    _GLOBAL_ACCOUNT_ID = account_id


def get_global_account_id() -> UUID | None:
    """Get the global account ID (single-account mode).

    Returns:
        UUID of the account, or None if not set.
    """
    return _GLOBAL_ACCOUNT_ID


def get_filter_registry() -> FilterRegistry:
    """Get the singleton FilterRegistry instance.

    Returns:
        FilterRegistry: The global filter registry instance
    """
    return FilterRegistry()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session


async def get_trade_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TradeRepository:
    """Get TradeRepository instance for dependency injection.

    Args:
        session: Database session from get_db_session

    Returns:
        TradeRepository: Trade repository instance
    """
    return TradeRepository(session)


# TODO: Add more dependency functions as needed:
# - get_bingx_client()
# - get_grid_manager()
# - get_current_user() (for authentication)
