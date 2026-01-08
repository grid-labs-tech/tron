from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.services.webapp import WebappService
import app.schemas.webapp as WebappSchemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user

router = APIRouter(prefix="/application_components/webapp", tags=["webapp"])


@router.post("/", response_model=WebappSchemas.Webapp)
def create_webapp(
    webapp: WebappSchemas.WebappCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WebappService.upsert_webapp(db=db, webapp=webapp)


@router.get("/", response_model=list[WebappSchemas.Webapp])
def list_webapps(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WebappService.get_webapps(db=db, skip=skip, limit=limit)


@router.get("/{uuid}", response_model=WebappSchemas.Webapp)
def get_webapp(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WebappService.get_webapp(db=db, uuid=uuid)


@router.put("/{uuid}", response_model=WebappSchemas.Webapp)
def update_webapp(
    uuid: UUID,
    webapp: WebappSchemas.WebappUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WebappService.upsert_webapp(db=db, webapp=webapp, uuid=uuid)


@router.delete("/{uuid}")
def delete_webapp(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WebappService.delete_webapp(db=db, uuid=uuid)


@router.get("/{uuid}/pods", response_model=list[WebappSchemas.Pod])
def get_webapp_pods(
    uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WebappService.get_webapp_pods(db=db, uuid=uuid)


@router.delete("/{uuid}/pods/{pod_name}")
def delete_webapp_pod(
    uuid: UUID,
    pod_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WebappService.delete_webapp_pod(db=db, uuid=uuid, pod_name=pod_name)


@router.get("/{uuid}/pods/{pod_name}/logs", response_model=WebappSchemas.PodLogs)
def get_webapp_pod_logs(
    uuid: UUID,
    pod_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return WebappService.get_webapp_pod_logs(
        db=db,
        uuid=uuid,
        pod_name=pod_name,
        container_name=container_name,
        tail_lines=tail_lines
    )


@router.post("/{uuid}/pods/{pod_name}/exec", response_model=WebappSchemas.PodCommandResponse)
def exec_webapp_pod_command(
    uuid: UUID,
    pod_name: str,
    request: WebappSchemas.PodCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return WebappService.exec_webapp_pod_command(
        db=db,
        uuid=uuid,
        pod_name=pod_name,
        command=request.command,
        container_name=request.container_name
    )

