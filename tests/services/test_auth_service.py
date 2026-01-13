"""Tests for AuthService."""

import os
from uuid import uuid4

import jwt
import pytest
from sqlalchemy.orm import Session

from src.services.auth_service import AuthService


@pytest.fixture
def jwt_secret() -> str:
    """JWT secret key for testing."""
    return "test-secret-key-for-jwt-tokens-minimum-32-chars"  # pragma: allowlist secret


@pytest.fixture
def auth_service(session: Session, jwt_secret: str) -> AuthService:
    """Create AuthService instance."""
    return AuthService(
        session,
        jwt_secret=jwt_secret,
        jwt_expiration_hours=24,
    )


class TestAuthService:
    """Test cases for AuthService."""

    def test_hash_password(self, auth_service: AuthService):
        """Test password hashing."""
        # Act
        hashed = auth_service.hash_password("mypassword123")

        # Assert
        assert hashed != "mypassword123"
        assert len(hashed) > 20  # bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # bcrypt hash format

    def test_hash_password_different_salts(self, auth_service: AuthService):
        """Test that same password produces different hashes."""
        # Act
        hash1 = auth_service.hash_password("samepassword")
        hash2 = auth_service.hash_password("samepassword")

        # Assert
        assert hash1 != hash2  # Different salts produce different hashes

    def test_verify_password_correct(self, auth_service: AuthService):
        """Test password verification with correct password."""
        # Arrange
        password = "testpassword123"  # pragma: allowlist secret
        hashed = auth_service.hash_password(password)

        # Act
        is_valid = auth_service.verify_password(password, hashed)

        # Assert
        assert is_valid is True

    def test_verify_password_incorrect(self, auth_service: AuthService):
        """Test password verification with incorrect password."""
        # Arrange
        hashed = auth_service.hash_password("correctpassword")

        # Act
        is_valid = auth_service.verify_password("wrongpassword", hashed)

        # Assert
        assert is_valid is False

    def test_register_success(self, auth_service: AuthService):
        """Test successful user registration."""
        # Act
        user = auth_service.register(
            email="newuser@example.com",
            password="password123",  # pragma: allowlist secret
            name="New User",
        )

        # Assert
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.is_active is True
        assert (
            user.password_hash != "password123"  # pragma: allowlist secret
        )  # Password should be hashed
        assert auth_service.verify_password(
            "password123",  # pragma: allowlist secret
            user.password_hash,
        )

    def test_register_password_too_short(self, auth_service: AuthService):
        """Test registration with too short password."""
        # Act & Assert
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.register(
                email="short@example.com",
                password="short",  # pragma: allowlist secret
            )

    def test_register_duplicate_email(self, auth_service: AuthService):
        """Test registration with duplicate email."""
        # Arrange
        auth_service.register(
            email="duplicate@example.com",
            password="password123",  # pragma: allowlist secret
        )

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            auth_service.register(
                email="duplicate@example.com",
                password="anotherpass123",  # pragma: allowlist secret
            )

    def test_login_success(self, auth_service: AuthService):
        """Test successful login."""
        # Arrange
        auth_service.register(
            email="login@example.com",
            password="mypassword123",  # pragma: allowlist secret
        )

        # Act
        user, token = auth_service.login(
            "login@example.com", "mypassword123"
        )  # pragma: allowlist secret

        # Assert
        assert user.email == "login@example.com"
        assert isinstance(token, str)
        assert len(token) > 20  # JWT tokens are long

    def test_login_wrong_email(self, auth_service: AuthService):
        """Test login with non-existent email."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.login("notfound@example.com", "password123")

    def test_login_wrong_password(self, auth_service: AuthService):
        """Test login with incorrect password."""
        # Arrange
        auth_service.register(
            email="wrongpass@example.com",
            password="correctpass123",  # pragma: allowlist secret
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.login("wrongpass@example.com", "wrongpass123")  # pragma: allowlist secret

    def test_login_inactive_account(self, auth_service: AuthService):
        """Test login with inactive account."""
        # Arrange
        user = auth_service.register(
            email="inactive@example.com",
            password="password123",  # pragma: allowlist secret
        )
        # Deactivate user
        auth_service.user_repository.deactivate_user(user.id)

        # Act & Assert
        with pytest.raises(ValueError, match="inactive"):
            auth_service.login("inactive@example.com", "password123")  # pragma: allowlist secret

    def test_verify_token_valid(self, auth_service: AuthService):
        """Test verifying valid token."""
        # Arrange
        registered_user = auth_service.register(
            email="tokentest@example.com",
            password="password123",  # pragma: allowlist secret
        )
        _, token = auth_service.login("tokentest@example.com", "password123")  # pragma: allowlist secret

        # Act
        user = auth_service.verify_token(token)

        # Assert
        assert user is not None
        assert user.id == registered_user.id
        assert user.email == "tokentest@example.com"

    def test_verify_token_invalid(self, auth_service: AuthService):
        """Test verifying invalid token."""
        # Act
        user = auth_service.verify_token("invalid.token.here")

        # Assert
        assert user is None

    def test_verify_token_expired(self, auth_service: AuthService, jwt_secret: str):
        """Test verifying expired token."""
        # Arrange
        user = auth_service.register(
            email="expired@example.com",
            password="password123",
        )

        # Create expired token (exp = 0)
        expired_token = jwt.encode(
            {"user_id": str(user.id), "email": user.email, "exp": 0},
            jwt_secret,
            algorithm="HS256",
        )

        # Act
        verified_user = auth_service.verify_token(expired_token)

        # Assert
        assert verified_user is None

    def test_verify_token_inactive_user(self, auth_service: AuthService):
        """Test verifying token for inactive user."""
        # Arrange
        user = auth_service.register(
            email="deactivated@example.com",
            password="password123",
        )
        _, token = auth_service.login("deactivated@example.com", "password123")

        # Deactivate user
        auth_service.user_repository.deactivate_user(user.id)

        # Act
        verified_user = auth_service.verify_token(token)

        # Assert
        assert verified_user is None  # Inactive users should not be verified

    def test_change_password_success(self, auth_service: AuthService):
        """Test changing password successfully."""
        # Arrange
        user = auth_service.register(
            email="changepass@example.com",
            password="oldpassword123",  # pragma: allowlist secret
        )

        # Act
        success = auth_service.change_password(
            user.id,
            "oldpassword123",  # pragma: allowlist secret
            "newpassword456",  # pragma: allowlist secret
        )

        # Assert
        assert success is True

        # Verify new password works
        logged_user, _ = auth_service.login(
            "changepass@example.com", "newpassword456"
        )  # pragma: allowlist secret
        assert logged_user.id == user.id

    def test_change_password_wrong_old_password(self, auth_service: AuthService):
        """Test changing password with incorrect old password."""
        # Arrange
        user = auth_service.register(
            email="wrongold@example.com",
            password="correctold123",  # pragma: allowlist secret
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Current password is incorrect"):
            auth_service.change_password(
                user.id,
                "wrongold123",  # pragma: allowlist secret
                "newpassword456",  # pragma: allowlist secret
            )

    def test_change_password_new_too_short(self, auth_service: AuthService):
        """Test changing password with too short new password."""
        # Arrange
        user = auth_service.register(
            email="shortNew@example.com",
            password="oldpassword123",  # pragma: allowlist secret
        )

        # Act & Assert
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.change_password(
                user.id,
                "oldpassword123",  # pragma: allowlist secret
                "short",  # pragma: allowlist secret
            )

    def test_change_password_user_not_found(self, auth_service: AuthService):
        """Test changing password for non-existent user."""
        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            auth_service.change_password(
                uuid4(),
                "oldpass123",
                "newpass123",
            )

    def test_jwt_secret_from_env_var(self, session: Session):
        """Test JWT secret loaded from environment variable."""
        # Arrange
        os.environ["JWT_SECRET_KEY"] = "env-secret-key-for-testing"  # pragma: allowlist secret

        try:
            # Act
            service = AuthService(session)

            # Assert
            assert service.jwt_secret == "env-secret-key-for-testing"  # pragma: allowlist secret
        finally:
            # Cleanup
            del os.environ["JWT_SECRET_KEY"]

    def test_missing_jwt_secret_raises_error(self, session: Session):
        """Test that missing JWT secret raises ValueError."""
        # Ensure env var is not set
        if "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]

        # Act & Assert
        with pytest.raises(ValueError, match="JWT secret key is required"):
            AuthService(session)

    def test_generate_token_contains_correct_payload(
        self,
        auth_service: AuthService,
        jwt_secret: str,
    ):
        """Test that generated token contains correct user information."""
        # Arrange
        user = auth_service.register(
            email="payload@example.com",
            password="password123",
        )
        _, token = auth_service.login("payload@example.com", "password123")

        # Act
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])

        # Assert
        assert payload["user_id"] == str(user.id)
        assert payload["email"] == "payload@example.com"
        assert "exp" in payload
        assert "iat" in payload
