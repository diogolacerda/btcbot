"""Authentication service for user management."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.database.repositories.user_repository import UserRepository
from src.utils.logger import main_logger


class AuthService:
    """Service for user authentication and management.

    Handles user registration, login, password hashing, and JWT token generation.

    Attributes:
        user_repository: Repository for user database operations.
        jwt_secret: Secret key for JWT token signing.
        jwt_algorithm: Algorithm for JWT token signing (default: HS256).
        jwt_expiration_hours: Token expiration time in hours (default: 24).
    """

    def __init__(
        self,
        session: Session,
        *,
        jwt_secret: str | None = None,
        jwt_algorithm: str = "HS256",
        jwt_expiration_hours: int = 24,
    ):
        """Initialize AuthService.

        Args:
            session: Database session.
            jwt_secret: Secret key for JWT (defaults to JWT_SECRET_KEY env var).
            jwt_algorithm: JWT algorithm (default: HS256).
            jwt_expiration_hours: Token expiration in hours (default: 24).

        Raises:
            ValueError: If jwt_secret is not provided and JWT_SECRET_KEY env var is not set.
        """
        self.user_repository = UserRepository(session)
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret:
            raise ValueError(
                "JWT secret key is required. Set JWT_SECRET_KEY environment variable or pass jwt_secret parameter."
            )
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiration_hours = jwt_expiration_hours

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password.

        Returns:
            Hashed password as a string.
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")  # type: ignore[no-any-return]

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Plain text password.
            hashed: Hashed password to compare against.

        Returns:
            True if password matches hash, False otherwise.
        """
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)  # type: ignore[no-any-return]

    def _generate_token(self, user_id: UUID, email: str) -> str:
        """Generate JWT token for a user.

        Args:
            user_id: User UUID.
            email: User email.

        Returns:
            JWT token as a string.
        """
        expiration = datetime.now(UTC) + timedelta(hours=self.jwt_expiration_hours)
        payload = {
            "user_id": str(user_id),
            "email": email,
            "exp": expiration.timestamp(),
            "iat": datetime.now(UTC).timestamp(),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token  # type: ignore[no-any-return]

    def register(
        self,
        email: str,
        password: str,
        *,
        name: str | None = None,
    ) -> User:
        """Register a new user.

        Args:
            email: User email address (must be unique).
            password: Plain text password (will be hashed).
            name: Optional display name.

        Returns:
            Created User instance.

        Raises:
            ValueError: If password is too short or email already exists.
            Exception: If database operation fails.
        """
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check if email already exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Hash password and create user
        password_hash = self.hash_password(password)
        try:
            user = self.user_repository.create_user(
                email=email,
                password_hash=password_hash,
                name=name,
            )
            main_logger.info(f"User registered: {user.email}")
            return user
        except Exception as e:
            main_logger.error(f"Error registering user {email}: {e}")
            raise

    def login(self, email: str, password: str) -> tuple[User, str]:
        """Authenticate a user and generate JWT token.

        Args:
            email: User email address.
            password: Plain text password.

        Returns:
            Tuple of (User instance, JWT token).

        Raises:
            ValueError: If credentials are invalid or account is inactive.
            Exception: If database operation fails.
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Check if account is active
        if not user.is_active:
            raise ValueError("Account is inactive")

        # Generate token
        token = self._generate_token(user.id, user.email)
        main_logger.info(f"User logged in: {user.email}")
        return user, token

    def verify_token(self, token: str) -> User | None:
        """Verify JWT token and return associated user.

        Args:
            token: JWT token to verify.

        Returns:
            User instance if token is valid, None otherwise.
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Extract user_id
            user_id_str = payload.get("user_id")
            if not user_id_str:
                return None

            user_id = UUID(user_id_str)

            # Get user from database
            user = self.user_repository.get_by_id(user_id)

            # Check if user exists and is active
            if not user or not user.is_active:
                return None

            return user
        except jwt.ExpiredSignatureError:
            main_logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            main_logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            main_logger.error(f"Error verifying token: {e}")
            return None

    def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user password.

        Args:
            user_id: User UUID.
            old_password: Current password for verification.
            new_password: New password to set.

        Returns:
            True if password was changed successfully.

        Raises:
            ValueError: If old password is incorrect or new password is too short.
            Exception: If database operation fails.
        """
        # Validate new password strength
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long")

        # Get user
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Verify old password
        if not self.verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Hash new password and update
        new_password_hash = self.hash_password(new_password)
        try:
            self.user_repository.update_user(
                user_id,
                password_hash=new_password_hash,
            )
            main_logger.info(f"Password changed for user {user.email}")
            return True
        except Exception as e:
            main_logger.error(f"Error changing password for user {user_id}: {e}")
            raise
