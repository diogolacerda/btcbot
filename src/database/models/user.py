"""User model for authentication and user management."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class User(Base):
    """User model for system authentication.

    Stores user credentials and basic profile information.
    Does not use external authentication providers (Auth0/Firebase).

    Attributes:
        id: Unique user identifier (UUID).
        email: User email address (unique).
        password_hash: Hashed password for authentication.
        name: Optional display name.
        is_active: Whether the user account is active.
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
