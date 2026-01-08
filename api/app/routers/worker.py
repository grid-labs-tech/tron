from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.services.worker import WorkerService
import app.schemas.worker as WorkerSchemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user

router = APIRouter(prefix="/application_components/worker", tags=["worker"])


@router.post("/", response_model=WorkerSchemas.Worker)
def create_worker(
    worker: WorkerSchemas.WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WorkerService.upsert_worker(db=db, worker=worker)


@router.get("/", response_model=list[WorkerSchemas.Worker])
def list_workers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WorkerService.get_workers(db=db, skip=skip, limit=limit)


@router.get("/{uuid}", response_model=WorkerSchemas.Worker)
def get_worker(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WorkerService.get_worker(db=db, uuid=uuid)


@router.put("/{uuid}", response_model=WorkerSchemas.Worker)
def update_worker(
    uuid: UUID,
    worker: WorkerSchemas.WorkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WorkerService.upsert_worker(db=db, worker=worker, uuid=uuid)


@router.delete("/{uuid}")
def delete_worker(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WorkerService.delete_worker(db=db, uuid=uuid)

