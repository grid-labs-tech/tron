from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database
from app.services.settings import SettingsService
from app.schemas import settings as schemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user
from uuid import UUID

router = APIRouter()


@router.post("/settings", response_model=schemas.Settings)
def create(
    setting: schemas.SettingsCreate,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return SettingsService.upsert(db, setting)


@router.put("/settings/{uuid}", response_model=schemas.Settings)
def update(
    setting: schemas.SettingsUpdate,
    uuid: UUID = None,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return SettingsService.upsert(db, setting, uuid)


@router.get("/settings/", response_model=list[schemas.SettingsWithEnvironment])
def list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return SettingsService.list(db, skip=skip, limit=limit)


@router.get("/settings/{uuid}", response_model=schemas.SettingsWithEnvironment)
def get_settings(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_settings = SettingsService.get(db, uuid=uuid)
    return db_settings


@router.delete("/settings/{uuid}", response_model=dict)
def delete(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return SettingsService.delete(db, uuid)
