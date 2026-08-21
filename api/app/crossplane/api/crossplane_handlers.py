# ruff: noqa: B008
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.clusters.infra.cluster_repository import ClusterRepository
from app.crossplane.api.crossplane_dto import (
    CrossplaneConfigResponse,
    CrossplaneConfigUpdate,
)
from app.crossplane.core.crossplane_service import CrossplaneService
from app.crossplane.infra.crossplane_config_repository import CrossplaneConfigRepository
from app.crossplane.infra.k8s_crossplane_probe import probe_crossplane_health
from app.environments.infra.environment_repository import EnvironmentRepository
from app.organizations.api.dependencies.organization_context import (
    getOrganizationContext,
)
from app.organizations.core.authorization import (
    OrganizationAccessContext,
    canManageEnvironmentByUuid,
    canViewEnvironment,
    isOrgAdmin,
)
from app.shared.database.database import get_db

router = APIRouter(
    prefix="/organizations/{organization_uuid}/environments/{environment_uuid}",
    tags=["crossplane"],
)


def get_crossplane_service(
    database_session: Session = Depends(get_db),
) -> CrossplaneService:
    cluster_repository = ClusterRepository(database_session)
    return CrossplaneService(
        CrossplaneConfigRepository(database_session),
        EnvironmentRepository(database_session),
        cluster_repository.find_by_uuid,
        probe_crossplane_health,
    )


@router.get("/crossplane", response_model=CrossplaneConfigResponse)
def get_crossplane_config(
    organization_uuid: UUID,
    environment_uuid: UUID,
    service: CrossplaneService = Depends(get_crossplane_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    db: Session = Depends(get_db),
):
    from app.environments.infra.environment_model import Environment as EnvironmentModel

    environment_model = (
        db.query(EnvironmentModel)
        .filter(
            EnvironmentModel.uuid == environment_uuid,
            EnvironmentModel.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not environment_model:
        raise HTTPException(status_code=404, detail="Environment not found")
    if not (isOrgAdmin(ctx) or canViewEnvironment(ctx, environment_model.id)):
        raise HTTPException(
            status_code=403,
            detail="Not allowed to view Crossplane config for this environment",
        )

    try:
        return service.get_config(environment_uuid, ctx.organization.id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/crossplane", response_model=CrossplaneConfigResponse)
def update_crossplane_config(
    organization_uuid: UUID,
    environment_uuid: UUID,
    payload: CrossplaneConfigUpdate,
    service: CrossplaneService = Depends(get_crossplane_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    db: Session = Depends(get_db),
):
    if not (isOrgAdmin(ctx) or canManageEnvironmentByUuid(ctx, environment_uuid, db)):
        raise HTTPException(
            status_code=403,
            detail="Not allowed to update Crossplane config for this environment",
        )
    try:
        return service.update_config(environment_uuid, payload, ctx.organization.id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
