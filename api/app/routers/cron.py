from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.services.cron import CronService
import app.schemas.cron as CronSchemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user

router = APIRouter(prefix="/application_components/cron", tags=["cron"])


@router.post("/", response_model=CronSchemas.Cron)
def create_cron(
    cron: CronSchemas.CronCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return CronService.upsert_cron(db=db, cron=cron)


@router.get("/", response_model=list[CronSchemas.Cron])
def list_crons(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CronService.get_crons(db=db, skip=skip, limit=limit)


@router.get("/{uuid}", response_model=CronSchemas.Cron)
def get_cron(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CronService.get_cron(db=db, uuid=uuid)


@router.put("/{uuid}", response_model=CronSchemas.Cron)
def update_cron(
    uuid: UUID,
    cron: CronSchemas.CronUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return CronService.upsert_cron(db=db, cron=cron, uuid=uuid)


@router.delete("/{uuid}")
def delete_cron(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return CronService.delete_cron(db=db, uuid=uuid)


@router.get("/{uuid}/jobs", response_model=list[CronSchemas.CronJob])
def get_cron_jobs(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CronService.get_cron_jobs(db=db, uuid=uuid)


@router.get("/{uuid}/jobs/{job_name}/logs", response_model=CronSchemas.CronJobLogs)
def get_cron_job_logs(
    uuid: UUID,
    job_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CronService.get_cron_job_logs(
        db=db,
        uuid=uuid,
        job_name=job_name,
        container_name=container_name,
        tail_lines=tail_lines
    )


@router.delete("/{uuid}/jobs/{job_name}")
def delete_cron_job(
    uuid: UUID,
    job_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return CronService.delete_cron_job(db=db, uuid=uuid, job_name=job_name)

