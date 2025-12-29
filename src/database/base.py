"""SQLAlchemy Base model for all database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models should inherit from this class to be picked up
    by Alembic for autogenerate migrations.
    """

    pass
