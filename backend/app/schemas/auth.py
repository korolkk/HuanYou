"""Auth schemas for request/response validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """User registration request."""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="user", pattern="^(user|shop_owner)$")
    email: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class UserLogin(BaseModel):
    """Login request."""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserInfo(BaseModel):
    """Public user information."""
    id: str
    phone: str
    name: Optional[str]
    role: str
    email: Optional[str]
    gender: Optional[str]


class UserUpdate(BaseModel):
    """Update user profile."""
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    wechat_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class ChangePassword(BaseModel):
    """Change password request."""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)
