"""User repository for managing user records."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.database.repositories.base_repository import BaseRepository
from src.utils.logger import main_logger


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD operations.

    Inherits from BaseRepository to leverage common CRUD operations
    while providing user-specific methods.

    Provides async methods for creating, reading, updating, and deleting
    user records for authentication and user management.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, User)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: User email address.

        Returns:
            User instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = select(User).where(User.email == email)
            result = self.session.execute(stmt)
            user: User | None = result.scalar_one_or_none()
            return user
        except Exception as e:
            main_logger.error(f"Error fetching user by email {email}: {e}")
            raise

    def list_active(self) -> list[User]:
        """Get all active users.

        Returns:
            List of User instances with is_active=True.

        Raises:
            Exception: If database operation fails.
        """
        try:
            stmt = select(User).where(User.is_active == True).order_by(User.created_at.desc())  # noqa: E712
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            main_logger.error(f"Error fetching active users: {e}")
            raise

    def create_user(
        self,
        email: str,
        password_hash: str,
        *,
        name: str | None = None,
        is_active: bool = True,
    ) -> User:
        """Create a new user.

        Uses BaseRepository.create() internally for database operations.

        Args:
            email: User email address (unique).
            password_hash: Hashed password.
            name: Optional display name.
            is_active: Whether the user account is active (default: True).

        Returns:
            Created User instance.

        Raises:
            Exception: If database operation fails (e.g., duplicate email).
        """
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                name=name,
                is_active=is_active,
            )
            created_user = super().create(user)
            main_logger.info(f"User created: {created_user.id} ({created_user.email})")
            return created_user
        except Exception as e:
            main_logger.error(f"Error creating user with email {email}: {e}")
            raise

    def update_user(
        self,
        user_id: UUID,
        **kwargs,
    ) -> User:
        """Update user fields.

        Uses BaseRepository.get_by_id() and update() internally.

        Args:
            user_id: User UUID.
            **kwargs: Fields to update (email, name, password_hash, is_active).

        Returns:
            Updated User instance.

        Raises:
            ValueError: If user is not found.
            Exception: If database operation fails.
        """
        try:
            user = super().get_by_id(user_id)

            if not user:
                raise ValueError(f"User {user_id} not found")

            # Update allowed fields
            for key, value in kwargs.items():
                if key in ("email", "name", "password_hash", "is_active"):
                    setattr(user, key, value)

            updated_user = super().update(user)
            main_logger.info(f"User {user_id} updated")
            return updated_user
        except ValueError:
            raise
        except Exception as e:
            main_logger.error(f"Error updating user {user_id}: {e}")
            raise

    def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate a user account.

        Args:
            user_id: User UUID.

        Returns:
            Updated User instance with is_active=False.

        Raises:
            ValueError: If user is not found.
            Exception: If database operation fails.
        """
        try:
            return self.update_user(user_id, is_active=False)
        except Exception as e:
            main_logger.error(f"Error deactivating user {user_id}: {e}")
            raise

    def activate_user(self, user_id: UUID) -> User:
        """Activate a user account.

        Args:
            user_id: User UUID.

        Returns:
            Updated User instance with is_active=True.

        Raises:
            ValueError: If user is not found.
            Exception: If database operation fails.
        """
        try:
            return self.update_user(user_id, is_active=True)
        except Exception as e:
            main_logger.error(f"Error activating user {user_id}: {e}")
            raise
