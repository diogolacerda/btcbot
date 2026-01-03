"""Authentication schemas for user management and JWT tokens."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str | None = Field(None, max_length=100, description="User's display name")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token payload."""

    email: str | None = None


class UserResponse(BaseModel):
    """User response schema (without password)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str | None
    is_active: bool
