"""Authentication routes for user management and JWT tokens."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    create_access_token,
    get_current_active_user,
    get_db,
    get_password_hash,
    verify_password,
)
from src.api.schemas.auth import Token, UserCreate, UserResponse
from src.database.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate user and return JWT access token.

    Args:
        form_data: OAuth2 form containing username (email) and password.
        session: Database session.

    Returns:
        Token object with access_token and token_type.

    Raises:
        HTTPException: If credentials are invalid.
    """
    # Get user from database
    result = session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return Token(access_token=access_token)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> Token:
    """Register a new user and return JWT access token.

    Args:
        user_data: User registration data (email, password, name).
        session: Database session.

    Returns:
        Token object with access_token and token_type.

    Raises:
        HTTPException: If email already exists.
    """
    # Check if user already exists
    result = session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        is_active=True,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Create access token
    access_token = create_access_token(data={"sub": new_user.email})

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token.

    Returns:
        UserResponse with user details (excluding password).
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
    )
