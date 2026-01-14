"""Tests for User model."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import User


class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self, session: Session):
        """Test creating a user with all fields."""
        # Arrange
        user = User(
            email="test@example.com",
            password_hash="hashed_password_123",  # pragma: allowlist secret
            name="Test User",
            is_active=True,
        )

        # Act
        session.add(user)
        session.commit()
        session.refresh(user)

        # Assert
        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"  # pragma: allowlist secret
        assert user.name == "Test User"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_create_user_minimal(self, session: Session):
        """Test creating a user with only required fields."""
        # Arrange
        user = User(
            email="minimal@example.com",
            password_hash="hashed_password_123",  # pragma: allowlist secret
        )

        # Act
        session.add(user)
        session.commit()
        session.refresh(user)

        # Assert
        assert user.id is not None
        assert user.email == "minimal@example.com"
        assert user.password_hash == "hashed_password_123"  # pragma: allowlist secret
        assert user.name is None
        assert user.is_active is True  # Default value

    def test_email_unique_constraint(self, session: Session):
        """Test that email must be unique."""
        # Arrange
        user1 = User(
            email="duplicate@example.com",
            password_hash="password1",  # pragma: allowlist secret
        )
        user2 = User(
            email="duplicate@example.com",
            password_hash="password2",  # pragma: allowlist secret
        )

        # Act & Assert
        session.add(user1)
        session.commit()

        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_email_required(self, session: Session):
        """Test that email is required."""
        # Arrange
        user = User(
            password_hash="password123",  # pragma: allowlist secret
        )

        # Act & Assert
        session.add(user)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_password_hash_required(self, session: Session):
        """Test that password_hash is required."""
        # Arrange
        user = User(
            email="test@example.com",
        )

        # Act & Assert
        session.add(user)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_is_active_default(self, session: Session):
        """Test that is_active defaults to True."""
        # Arrange
        user = User(
            email="active@example.com",
            password_hash="password123",  # pragma: allowlist secret
        )

        # Act
        session.add(user)
        session.commit()
        session.refresh(user)

        # Assert
        assert user.is_active is True

    def test_is_active_can_be_false(self, session: Session):
        """Test that is_active can be set to False."""
        # Arrange
        user = User(
            email="inactive@example.com",
            password_hash="password123",  # pragma: allowlist secret
            is_active=False,
        )

        # Act
        session.add(user)
        session.commit()
        session.refresh(user)

        # Assert
        assert user.is_active is False

    def test_timestamps_auto_generated(self, session: Session):
        """Test that timestamps are automatically generated."""
        # Arrange
        user = User(
            email="timestamps@example.com",
            password_hash="password123",  # pragma: allowlist secret
        )

        # Act
        session.add(user)
        session.commit()
        session.refresh(user)

        # Assert
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_updated_at_changes_on_update(self, session: Session):
        """Test that updated_at changes when user is updated."""
        # Arrange
        user = User(
            email="update@example.com",
            password_hash="password123",  # pragma: allowlist secret
            name="Original Name",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        original_updated_at = user.updated_at

        # Act - Update the user
        user.name = "Updated Name"
        session.commit()
        session.refresh(user)

        # Assert
        assert user.updated_at > original_updated_at
        assert user.name == "Updated Name"

    def test_query_by_email(self, session: Session):
        """Test querying user by email."""
        # Arrange
        user = User(
            email="query@example.com",
            password_hash="password123",  # pragma: allowlist secret
            name="Query User",
        )
        session.add(user)
        session.commit()

        # Act
        stmt = select(User).where(User.email == "query@example.com")
        result = session.execute(stmt)
        found_user = result.scalar_one_or_none()

        # Assert
        assert found_user is not None
        assert found_user.email == "query@example.com"
        assert found_user.name == "Query User"

    def test_query_by_is_active(self, session: Session):
        """Test querying users by is_active status."""
        # Arrange
        active_user = User(
            email="active@example.com",
            password_hash="password1",  # pragma: allowlist secret
            is_active=True,
        )
        inactive_user = User(
            email="inactive@example.com",
            password_hash="password2",  # pragma: allowlist secret
            is_active=False,
        )
        session.add_all([active_user, inactive_user])
        session.commit()

        # Act
        stmt = select(User).where(User.is_active == True)  # noqa: E712
        result = session.execute(stmt)
        active_users = result.scalars().all()

        # Assert
        assert len(active_users) == 1
        assert active_users[0].email == "active@example.com"

    def test_user_repr(self, session: Session):
        """Test User __repr__ method."""
        # Arrange
        user = User(
            email="repr@example.com",
            password_hash="password123",  # pragma: allowlist secret
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Act
        repr_str = repr(user)

        # Assert
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "repr@example.com" in repr_str
        assert "is_active=True" in repr_str
