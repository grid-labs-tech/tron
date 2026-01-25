from pydantic import BaseModel, field_validator
from typing import Optional

from app.shared.utils.validators import (
    validate_email_permissive,
    validate_email_optional,
)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    uuid: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_permissive(v)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None  # Required to change password

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        return validate_email_optional(v)
