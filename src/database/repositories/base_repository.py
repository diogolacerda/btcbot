"""Generic base repository with CRUD operations.

This module provides a generic base repository that implements standard CRUD
operations, allowing specific repositories to inherit this functionality and
implement only custom methods.

Type safety is ensured through the use of TypeVar, allowing the repository
to work with any SQLAlchemy model that inherits from Base.
"""

from typing import TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import Base

# TypeVar for generic model typing
T = TypeVar("T", bound=Base)


class BaseRepository[T: Base]:
    """Generic repository for basic CRUD operations.

    This class provides standard database operations that can be inherited
    by specific repositories, reducing code duplication and ensuring
    consistency across all repository implementations.

    Type Parameters:
        T: The SQLAlchemy model type (must inherit from Base).

    Attributes:
        session: Async SQLAlchemy session for database operations.
        model: The SQLAlchemy model class.

    Example:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)

            # Add custom methods here
            async def get_by_email(self, email: str) -> User | None:
                ...
    """

    def __init__(self, session: AsyncSession, model: type[T]):
        """Initialize repository with database session and model.

        Args:
            session: Async database session.
            model: The SQLAlchemy model class for this repository.
        """
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID) -> T | None:
        """Get a record by its ID.

        Args:
            id: UUID of the record to retrieve.

        Returns:
            Model instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.

        Example:
            user = await repo.get_by_id(user_id)
            if user:
                print(f"Found user: {user.name}")
        """
        try:
            result = await self.session.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            raise Exception(f"Error fetching {self.model.__name__} by id {id}: {e}") from e

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all records with pagination support.

        Args:
            skip: Number of records to skip (offset). Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            List of model instances.

        Raises:
            Exception: If database operation fails.

        Example:
            # Get first 10 users
            users = await repo.get_all(skip=0, limit=10)

            # Get next 10 users
            users = await repo.get_all(skip=10, limit=10)
        """
        try:
            result = await self.session.execute(
                select(self.model).offset(skip).limit(limit).order_by(self.model.id)
            )
            return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Error fetching all {self.model.__name__} records: {e}") from e

    async def create(self, obj: T) -> T:
        """Create a new record.

        Args:
            obj: Model instance to create.

        Returns:
            Created and refreshed model instance with database-generated fields.

        Raises:
            Exception: If database operation fails (including integrity errors).

        Example:
            user = User(name="John", email="john@example.com")
            created_user = await repo.create(user)
            print(f"Created user with ID: {created_user.id}")
        """
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error creating {self.model.__name__}: {e}") from e

    async def update(self, obj: T) -> T:
        """Update an existing record.

        The object should already have modifications applied. This method
        commits those changes to the database.

        Args:
            obj: Modified model instance to update.

        Returns:
            Updated and refreshed model instance.

        Raises:
            Exception: If database operation fails.

        Example:
            user = await repo.get_by_id(user_id)
            if user:
                user.name = "Jane"
                updated_user = await repo.update(user)
        """
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error updating {self.model.__name__}: {e}") from e

    async def delete(self, id: UUID) -> bool:
        """Delete a record by its ID.

        Args:
            id: UUID of the record to delete.

        Returns:
            True if record was deleted, False if record was not found.

        Raises:
            Exception: If database operation fails.

        Example:
            deleted = await repo.delete(user_id)
            if deleted:
                print("User deleted successfully")
            else:
                print("User not found")
        """
        try:
            result = await self.session.execute(delete(self.model).where(self.model.id == id))
            await self.session.commit()
            return result.rowcount > 0  # type: ignore[no-any-return]
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error deleting {self.model.__name__} with id {id}: {e}") from e

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists by its ID.

        Args:
            id: UUID of the record to check.

        Returns:
            True if record exists, False otherwise.

        Raises:
            Exception: If database operation fails.

        Example:
            if await repo.exists(user_id):
                print("User exists")
            else:
                print("User not found")
        """
        try:
            result = await self.session.execute(select(self.model.id).where(self.model.id == id))
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise Exception(
                f"Error checking existence of {self.model.__name__} with id {id}: {e}"
            ) from e
