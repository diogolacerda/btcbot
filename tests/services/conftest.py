"""Pytest fixtures for service tests."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.base import Base


@pytest.fixture(scope="function")
def engine():
    """Create test database engine.

    Uses in-memory SQLite for fast isolated tests.
    Foreign key constraints are enabled for proper FK testing.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Drop all tables
    Base.metadata.drop_all(engine)

    engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Generator[Session, None, None]:
    """Create test database session."""
    session_maker = sessionmaker(
        engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = session_maker()
    yield session
    session.rollback()
    session.close()
