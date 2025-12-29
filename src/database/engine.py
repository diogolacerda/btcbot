"""Database engine and session configuration."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_database_url() -> str:
    """Get database URL from environment.

    Returns the DATABASE_URL environment variable, converting postgresql://
    to postgresql+asyncpg:// for async driver support.
    """
    url = os.getenv("DATABASE_URL", "postgresql://btcbot:btcbot_dev@localhost:5433/btcbot_dev")

    # Convert to async driver URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def get_engine(echo: bool = False):
    """Create async database engine.

    Args:
        echo: If True, log all SQL statements (useful for debugging).

    Returns:
        AsyncEngine instance.
    """
    return create_async_engine(
        get_database_url(),
        echo=echo,
        pool_pre_ping=True,
    )


def get_session_maker(engine=None) -> async_sessionmaker[AsyncSession]:
    """Create async session maker.

    Args:
        engine: Optional engine instance. If not provided, creates a new one.

    Returns:
        Async session maker.
    """
    if engine is None:
        engine = get_engine()

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession instance.

    Usage:
        async for session in get_session():
            # use session
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session
