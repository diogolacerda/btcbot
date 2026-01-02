"""Tests for UserRepository."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.user_repository import UserRepository


@pytest.fixture
async def repository(async_session: AsyncSession) -> UserRepository:
    """Create UserRepository instance."""
    return UserRepository(async_session)


class TestUserRepository:
    """Test cases for UserRepository."""

    @pytest.mark.asyncio
    async def test_create_user(self, repository: UserRepository):
        """Test creating a user."""
        # Act
        user = await repository.create_user(
            email="test@example.com",
            password_hash="hashed_password",  # pragma: allowlist secret
            name="Test User",
        )

        # Assert
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"  # pragma: allowlist secret
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_user_minimal(self, repository: UserRepository):
        """Test creating a user with minimal data."""
        # Act
        user = await repository.create_user(
            email="minimal@example.com",
            password_hash="hashed",  # pragma: allowlist secret
        )

        # Assert
        assert user.id is not None
        assert user.email == "minimal@example.com"
        assert user.name is None
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_inactive_user(self, repository: UserRepository):
        """Test creating an inactive user."""
        # Act
        user = await repository.create_user(
            email="inactive@example.com",
            password_hash="hashed",  # pragma: allowlist secret
            is_active=False,
        )

        # Assert
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_unique_email_constraint(self, repository: UserRepository):
        """Test unique constraint on email."""
        # Arrange
        await repository.create_user(
            email="duplicate@example.com",
            password_hash="hash1",  # pragma: allowlist secret
        )

        # Act & Assert - Repository wraps IntegrityError in Exception
        with pytest.raises(Exception, match=""):
            await repository.create_user(
                email="duplicate@example.com",
                password_hash="hash2",  # pragma: allowlist secret
            )

    @pytest.mark.asyncio
    async def test_get_by_id(self, repository: UserRepository):
        """Test getting user by ID."""
        # Arrange
        created_user = await repository.create_user(
            email="getbyid@example.com",
            password_hash="hash",  # pragma: allowlist secret
        )

        # Act
        user = await repository.get_by_id(created_user.id)

        # Assert
        assert user is not None
        assert user.id == created_user.id
        assert user.email == "getbyid@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: UserRepository):
        """Test getting user by non-existent ID."""
        # Act
        user = await repository.get_by_id(uuid4())

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, repository: UserRepository):
        """Test getting user by email."""
        # Arrange
        await repository.create_user(
            email="findme@example.com",
            password_hash="hash",  # pragma: allowlist secret
        )

        # Act
        user = await repository.get_by_email("findme@example.com")

        # Assert
        assert user is not None
        assert user.email == "findme@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repository: UserRepository):
        """Test getting user by non-existent email."""
        # Act
        user = await repository.get_by_email("notfound@example.com")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_list_active(self, repository: UserRepository):
        """Test listing active users."""
        # Arrange
        await repository.create_user(
            email="active1@example.com",
            password_hash="hash",  # pragma: allowlist secret
            is_active=True,
        )
        await repository.create_user(
            email="active2@example.com",
            password_hash="hash",  # pragma: allowlist secret
            is_active=True,
        )
        await repository.create_user(
            email="inactive@example.com",
            password_hash="hash",  # pragma: allowlist secret
            is_active=False,
        )

        # Act
        active_users = await repository.list_active()

        # Assert
        assert len(active_users) == 2
        assert all(user.is_active for user in active_users)
        emails = [user.email for user in active_users]
        assert "active1@example.com" in emails
        assert "active2@example.com" in emails
        assert "inactive@example.com" not in emails

    @pytest.mark.asyncio
    async def test_update_user(self, repository: UserRepository):
        """Test updating user fields."""
        # Arrange
        user = await repository.create_user(
            email="update@example.com",
            password_hash="old_hash",  # pragma: allowlist secret
            name="Old Name",
        )

        # Act
        updated_user = await repository.update_user(
            user.id,
            name="New Name",
            password_hash="new_hash",  # pragma: allowlist secret
        )

        # Assert
        assert updated_user.name == "New Name"
        assert updated_user.password_hash == "new_hash"  # pragma: allowlist secret
        assert updated_user.email == "update@example.com"  # Email unchanged

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, repository: UserRepository):
        """Test updating non-existent user."""
        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await repository.update_user(uuid4(), name="New Name")

    @pytest.mark.asyncio
    async def test_deactivate_user(self, repository: UserRepository):
        """Test deactivating a user."""
        # Arrange
        user = await repository.create_user(
            email="deactivate@example.com",
            password_hash="hash",  # pragma: allowlist secret
            is_active=True,
        )

        # Act
        deactivated = await repository.deactivate_user(user.id)

        # Assert
        assert deactivated.is_active is False
        assert deactivated.id == user.id

    @pytest.mark.asyncio
    async def test_activate_user(self, repository: UserRepository):
        """Test activating a user."""
        # Arrange
        user = await repository.create_user(
            email="activate@example.com",
            password_hash="hash",  # pragma: allowlist secret
            is_active=False,
        )

        # Act
        activated = await repository.activate_user(user.id)

        # Assert
        assert activated.is_active is True
        assert activated.id == user.id

    @pytest.mark.asyncio
    async def test_delete_user(self, repository: UserRepository):
        """Test deleting a user."""
        # Arrange
        user = await repository.create_user(
            email="delete@example.com",
            password_hash="hash",  # pragma: allowlist secret
        )

        # Act
        deleted = await repository.delete(user.id)

        # Assert
        assert deleted is True
        assert await repository.get_by_id(user.id) is None

    @pytest.mark.asyncio
    async def test_delete_non_existent_user(self, repository: UserRepository):
        """Test deleting non-existent user."""
        # Act
        deleted = await repository.delete(uuid4())

        # Assert
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self, repository: UserRepository):
        """Test checking if user exists."""
        # Arrange
        user = await repository.create_user(
            email="exists@example.com",
            password_hash="hash",  # pragma: allowlist secret
        )

        # Act & Assert
        assert await repository.exists(user.id) is True
        assert await repository.exists(uuid4()) is False

    @pytest.mark.asyncio
    async def test_get_all(self, repository: UserRepository):
        """Test getting all users with pagination."""
        # Arrange
        for i in range(5):
            await repository.create_user(
                email=f"user{i}@example.com",
                password_hash="hash",  # pragma: allowlist secret
            )

        # Act
        all_users = await repository.get_all(skip=0, limit=10)
        first_two = await repository.get_all(skip=0, limit=2)
        next_two = await repository.get_all(skip=2, limit=2)

        # Assert
        assert len(all_users) == 5
        assert len(first_two) == 2
        assert len(next_two) == 2
        assert first_two[0].id != next_two[0].id
