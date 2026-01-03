"""Shared dependencies for FastAPI endpoints.

This module provides dependency injection functions for:
- Database sessions
- BingX client
- GridManager instance
- Authentication
- Global account ID (single-account mode)
"""

from uuid import UUID

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
