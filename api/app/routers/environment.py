from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database
from app.services.environment import EnvironmentService
from app.schemas import environment as schemas
from app.models.user import UserRole
from app.dependencies.auth import require_role, get_current_user
from app.models.user import User
from uuid import UUID

router = APIRouter()


@router.post("/environments/", response_model=schemas.Environment)
def create_environment(
    environment: schemas.EnvironmentBase,
    uuid: UUID = None,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return EnvironmentService.upsert_environment(db, environment, uuid)


@router.put("/environments/{uuid}", response_model=schemas.Environment)
def update_environment(
    environment: schemas.EnvironmentBase,
    uuid: UUID = None,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return EnvironmentService.upsert_environment(db, environment, uuid)


@router.get("/environments/", response_model=list[schemas.EnvironmentWithClusters])
def list_environments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return EnvironmentService.get_environments(db, skip=skip, limit=limit)


@router.get("/environments/{uuid}", response_model=schemas.EnvironmentWithClusters)
def get_environment(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_environment = EnvironmentService.get_environment(db, environment_uuid=uuid)
    if db_environment is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    return db_environment


@router.delete("/environments/{uuid}", response_model=dict)
def delete_environment(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return EnvironmentService.delete_environment(db, uuid)
