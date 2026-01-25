"""DTOs for setup endpoints."""

from pydantic import BaseModel, EmailStr, Field


class SetupStatus(BaseModel):
    """Response for setup status check."""

    initialized: bool
    message: str


class SetupInitialize(BaseModel):
    """Request to initialize the system."""

    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_password: str = Field(..., min_length=6, description="Admin user password")
    admin_name: str = Field(default="Administrator", description="Admin user full name")
    # Kept for backward compatibility with older frontend versions
    organization_name: str = Field(
        default="", description="Organization name (not used)"
    )


class SetupInitializeResponse(BaseModel):
    """Response after successful initialization."""

    success: bool
    message: str
    admin_email: str
