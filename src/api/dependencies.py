"""Shared dependencies for FastAPI endpoints.

This module provides dependency injection functions for:
- Database sessions
- Repositories
- BingX client
- GridManager instance
- Filter registry
- Authentication (JWT tokens, password hashing)
- User retrieval
- Global account ID (single-account mode)
"""

import logging
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.auth import TokenData
from src.database import get_session
from src.database.models.user import User
from src.database.repositories.trade_repository import TradeRepository
from src.filters.registry import FilterRegistry
from src.grid.order_tracker import OrderTracker

logger = logging.getLogger(__name__)

# Global account ID for single-account mode
# Set during startup in main.py
_GLOBAL_ACCOUNT_ID: UUID | None = None

# Global OrderTracker reference for API access
# Set during bot startup in main.py
_ORDER_TRACKER: OrderTracker | None = None

# JWT Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-change-in-production"
)  # pragma: allowlist secret
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 days


def _validate_secret_key() -> None:
    """Validate SECRET_KEY strength and warn if using default or weak key.

    This function is called automatically when the module is imported.
    It checks:
    - If SECRET_KEY is the default value
    - If SECRET_KEY has sufficient entropy (minimum 32 characters)
    - Logs appropriate warnings for production environments
    """
    default_key = "your-secret-key-change-in-production"
    min_length = 32

    # Check if using default key
    if SECRET_KEY == default_key:
        logger.warning(
            "⚠️  SECURITY WARNING: Using default SECRET_KEY! "
            "This is INSECURE and should be changed immediately. "
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        return

    # Check minimum length for entropy
    if len(SECRET_KEY) < min_length:
        logger.warning(
            f"⚠️  SECURITY WARNING: SECRET_KEY is too short ({len(SECRET_KEY)} characters). "
            f"Minimum recommended length is {min_length} characters for adequate security. "
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        return

    # Check if key looks like a weak pattern (all same character, sequential, etc)
    if len(set(SECRET_KEY)) < 10:  # Less than 10 unique characters
        logger.warning(
            "⚠️  SECURITY WARNING: SECRET_KEY has low entropy (too few unique characters). "
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        return

    logger.debug(f"✓ SECRET_KEY validated successfully ({len(SECRET_KEY)} characters)")


# Validate SECRET_KEY on module import
_validate_secret_key()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password from user input.
        hashed_password: Hashed password from database.

    Returns:
        True if password matches, False otherwise.
    """
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return str(pwd_context.hash(password))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing token payload data.
        expires_delta: Optional expiration time delta. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (alias for get_db_session for auth routes).

    Yields:
        AsyncSession instance.
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


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header.
        session: Database session.

    Returns:
        User model instance.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except (jwt.InvalidTokenError, jwt.DecodeError, Exception):
        raise credentials_exception from None

    # Get user from database
    result = await session.execute(select(User).where(User.email == token_data.email))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user.

    Args:
        current_user: Current user from get_current_user dependency.

    Returns:
        User model instance if active.

    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def set_order_tracker(order_tracker: OrderTracker) -> None:
    """Set the global OrderTracker reference for API access.

    This is called during bot startup in main.py after GridManager is initialized.

    Args:
        order_tracker: The OrderTracker instance from GridManager.
    """
    global _ORDER_TRACKER
    _ORDER_TRACKER = order_tracker
    logger.debug("OrderTracker reference set for API access")


def get_order_tracker() -> OrderTracker | None:
    """Get the global OrderTracker reference.

    Returns:
        OrderTracker instance, or None if not set.
    """
    return _ORDER_TRACKER
