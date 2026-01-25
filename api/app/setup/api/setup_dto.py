"""DTOs for setup endpoints."""

from pydantic import BaseModel, Field, field_validator

from app.shared.utils.validators import validate_email_permissive


class SetupStatus(BaseModel):
    """Response for setup status check."""

    initialized: bool
    message: str


class SetupInitialize(BaseModel):
    """Request to initialize the system."""

    admin_email: str = Field(..., description="Admin user email")
    admin_password: str = Field(..., min_length=6, description="Admin user password")
    admin_name: str = Field(default="Administrator", description="Admin user full name")
    # Kept for backward compatibility with older frontend versions
    organization_name: str = Field(
        default="", description="Organization name (not used)"
    )

    @field_validator("admin_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_permissive(v)


class SetupInitializeResponse(BaseModel):
    """Response after successful initialization."""

    success: bool
    message: str
    admin_email: str
