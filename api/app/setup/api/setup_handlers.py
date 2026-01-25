"""Setup API handlers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.shared.database.database import get_db
from app.setup.core.setup_service import SetupService
from app.setup.api.setup_dto import (
    SetupStatus,
    SetupInitialize,
    SetupInitializeResponse,
)

router = APIRouter(prefix="/setup", tags=["Setup"])


def get_setup_service(db: Session = Depends(get_db)) -> SetupService:
    """Dependency to get SetupService instance."""
    return SetupService(db)


@router.get("/status", response_model=SetupStatus)
def get_setup_status(service: SetupService = Depends(get_setup_service)):
    """
    Check if the system has been initialized.

    Returns:
        SetupStatus with initialized flag and message
    """
    initialized = service.is_initialized()
    skip_setup = service.should_skip_setup()

    if skip_setup and not initialized:
        return SetupStatus(
            initialized=False,
            message="Setup skipped via SKIP_SETUP environment variable",
        )

    if initialized:
        return SetupStatus(
            initialized=True,
            message="System is ready",
        )

    return SetupStatus(
        initialized=False,
        message="System requires initial setup",
    )


@router.post("/initialize", response_model=SetupInitializeResponse)
def initialize_setup(
    data: SetupInitialize,
    service: SetupService = Depends(get_setup_service),
):
    """
    Initialize the system with the first admin user.

    This endpoint can only be called once, when no admin users exist.

    Args:
        data: SetupInitialize with admin credentials

    Returns:
        SetupInitializeResponse on success

    Raises:
        HTTPException 400: If system is already initialized
    """
    if service.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="System is already initialized. Cannot run setup again.",
        )

    try:
        admin_user = service.initialize(
            admin_email=data.admin_email,
            admin_password=data.admin_password,
            admin_name=data.admin_name,
        )

        return SetupInitializeResponse(
            success=True,
            message="System initialized successfully! You can now login with your admin credentials.",
            admin_email=admin_user.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize system: {str(e)}"
        )
