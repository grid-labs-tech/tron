from pydantic import BaseModel, ConfigDict, model_validator, field_validator
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

from app.shared.utils.validators import (
    validate_email_permissive,
    validate_email_optional,
)


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_permissive(v)


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        return validate_email_optional(v)


class UserResponse(UserBase):
    uuid: str
    is_active: bool
    role: str
    avatar_url: Optional[str] = None
    created_at: str
    updated_at: str

    @model_validator(mode="before")
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "uuid" in data and isinstance(data["uuid"], UUID):
                data["uuid"] = str(data["uuid"])
            if "created_at" in data and isinstance(data["created_at"], datetime):
                data["created_at"] = data["created_at"].isoformat()
            if "updated_at" in data and isinstance(data["updated_at"], datetime):
                data["updated_at"] = data["updated_at"].isoformat()
        elif hasattr(data, "__dict__"):
            if hasattr(data, "uuid") and isinstance(data.uuid, UUID):
                data.uuid = str(data.uuid)
            if hasattr(data, "created_at") and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, "updated_at") and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )
