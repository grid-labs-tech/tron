from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from .. import database
from app.services.instance import InstanceService
from app.schemas import instance as InstanceSchemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user

router = APIRouter()


@router.post("/instances/", response_model=InstanceSchemas.Instance)
def create_instance(
    instance: InstanceSchemas.InstanceCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return InstanceService.upsert_instance(db, instance)


@router.put("/instances/{uuid}", response_model=InstanceSchemas.Instance)
def update_instance(
    uuid: UUID,
    instance: InstanceSchemas.InstanceUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return InstanceService.update_instance(db, uuid, instance)


@router.get("/instances/", response_model=list[InstanceSchemas.Instance])
def list_instances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return InstanceService.get_instances(db, skip=skip, limit=limit)


@router.get("/instances/{uuid}", response_model=InstanceSchemas.Instance)
def get_instance(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_instance = InstanceService.get_instance(db, uuid=uuid)
    if db_instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    return db_instance


@router.delete("/instances/{uuid}", response_model=dict)
def delete_instance(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    return InstanceService.delete_instance(db, uuid)


@router.get("/instances/{uuid}/events", response_model=List[InstanceSchemas.KubernetesEvent])
def get_instance_events(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return InstanceService.get_instance_events(db, uuid)


@router.post("/instances/{uuid}/sync", response_model=dict)
def sync_instance(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """
    Sincroniza todos os componentes de uma instância com o Kubernetes.
    Reaplica componentes habilitados e remove componentes desabilitados.
    """
    return InstanceService.sync_instance(db, uuid)

