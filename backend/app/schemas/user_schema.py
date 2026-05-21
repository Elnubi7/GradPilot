from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=255)
    avatar_style: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Provide a valid email address.")
        return normalized


class UserRegisterRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=255)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: str | None = Field(default=None, min_length=5, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    avatar_style: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Provide a valid email address.")
        return normalized


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)


class UserResponse(UserBase):
    id: int
    created_at: datetime


class UserLoginResponse(BaseModel):
    success: bool
    user: UserResponse | None = None
    message: str


class FavoriteCreateRequest(BaseModel):
    user_id: int | None = None
    project_id: int


class FavoriteResponse(BaseModel):
    id: int
    user_id: int | None = None
    project_id: int
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
