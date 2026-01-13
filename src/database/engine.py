"""Database engine and session configuration."""

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Get database URL from environment.

    Returns the DATABASE_URL environment variable with psycopg2 driver.
    """
    url = os.getenv("DATABASE_URL", "postgresql://btcbot:btcbot_dev@localhost:5433/btcbot_dev")

    # Ensure we're using the standard psycopg2 driver (not asyncpg)
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    return url


def get_engine(echo: bool = False):
    """Create database engine.

    Args:
        echo: If True, log all SQL statements (useful for debugging).

    Returns:
        Engine instance.
    """
    return create_engine(
        get_database_url(),
        echo=echo,
        pool_pre_ping=True,
    )


def get_session_maker(engine=None) -> sessionmaker[Session]:
    """Create session maker.

    Args:
        engine: Optional engine instance. If not provided, creates a new one.

    Returns:
        Session maker.
    """
    if engine is None:
        engine = get_engine()

    return sessionmaker(
        engine,
        class_=Session,
        expire_on_commit=False,
    )


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get database session context manager.

    Yields:
        Session instance.

    Usage:
        with get_session() as session:
            # use session
    """
    session_maker = get_session_maker()
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
