from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.clusters.infra.cluster_repository import ClusterRepository
from app.clusters.core.cluster_service import ClusterService
from app.clusters.api.cluster_dto import (
    ClusterCreate,
    ClusterResponse,
    ClusterResponseWithValidation,
    ClusterCompletedResponse,
)
from app.clusters.core.cluster_validators import (
    ClusterNotFoundError,
    ClusterConnectionError,
    EnvironmentNotFoundError,
)
from app.crossplane.infra.k8s_crossplane_probe import probe_crossplane_health
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.core.environment_service import EnvironmentService
from app.organizations.api.dependencies.organization_context import (
    getOrganizationContext,
)
from app.organizations.core.authorization import (
    OrganizationAccessContext,
    isOrgAdmin,
    isOrgMember,
    canViewEnvironment,
    canViewApplication,
)


router = APIRouter(
    prefix="/organizations/{organization_uuid}/clusters", tags=["clusters"]
)

# Clusters by environment: /organizations/{org_uuid}/environments/{env_uuid}/clusters
router_env_clusters = APIRouter(
    prefix="/organizations/{organization_uuid}/environments/{environment_uuid}/clusters",
    tags=["clusters"],
)


def get_cluster_service(database_session: Session = Depends(get_db)) -> ClusterService:
    """Dependency to get ClusterService instance."""
    cluster_repository = ClusterRepository(database_session)
    return ClusterService(cluster_repository, probe_crossplane_health)


def get_environment_service(
    database_session: Session = Depends(get_db),
) -> EnvironmentService:
    """Dependency to get EnvironmentService instance."""
    environment_repository = EnvironmentRepository(database_session)
    return EnvironmentService(environment_repository)


@router.post("/", response_model=ClusterResponse)
def create_cluster(
    organization_uuid: UUID,
    cluster: ClusterCreate,
    service: ClusterService = Depends(get_cluster_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Create a new cluster within an organization."""
    # Only org admins can create clusters
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403, detail="Only organization admins can create clusters"
        )

    try:
        return service.create_cluster(cluster)
    except (EnvironmentNotFoundError, ClusterConnectionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{uuid}", response_model=ClusterResponse)
def update_cluster(
    organization_uuid: UUID,
    uuid: UUID,
    cluster: ClusterCreate,
    service: ClusterService = Depends(get_cluster_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Update an existing cluster."""
    # Only org admins can update clusters
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403, detail="Only organization admins can update clusters"
        )

    try:
        return service.update_cluster(uuid, cluster)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (EnvironmentNotFoundError, ClusterConnectionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ClusterResponseWithValidation])
def list_clusters(
    organization_uuid: UUID,
    skip: int = 0,
    limit: int = 100,
    service: ClusterService = Depends(get_cluster_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """List all clusters for an organization."""
    if not isOrgMember(ctx):
        raise HTTPException(
            status_code=403, detail="Only organization admins can list clusters"
        )

    return service.get_clusters(
        skip=skip, limit=limit, organization_id=ctx.organization.id
    )


@router.get("/{uuid}", response_model=ClusterCompletedResponse)
def get_cluster(
    organization_uuid: UUID,
    uuid: UUID,
    service: ClusterService = Depends(get_cluster_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Get cluster by UUID."""
    try:
        return service.get_cluster(uuid)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_env_clusters.get("/", response_model=list[ClusterResponseWithValidation])
def list_clusters_by_environment(
    organization_uuid: UUID,
    environment_uuid: UUID,
    skip: int = 0,
    limit: int = 100,
    service: ClusterService = Depends(get_cluster_service),
    env_service: EnvironmentService = Depends(get_environment_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    db: Session = Depends(get_db),
):
    """List clusters for an environment. Environment must belong to the organization."""
    try:
        environment_id = env_service.get_environment_id_for_organization(
            ctx.organization.id, environment_uuid
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Check if user can view environment
    can_view_env = canViewEnvironment(ctx, environment_id)

    # Check if user can view any application with instances in this environment
    can_view_app = False
    if not isOrgMember(ctx) and not can_view_env:
        from app.instances.infra.instance_model import Instance as InstanceModel

        instances_in_env = (
            db.query(InstanceModel)
            .filter(InstanceModel.environment_id == environment_id)
            .all()
        )

        for instance in instances_in_env:
            if canViewApplication(ctx, instance.application_id):
                can_view_app = True
                break

    if not isOrgMember(ctx) and not can_view_env and not can_view_app:
        raise HTTPException(
            status_code=403,
            detail="Only organization members, environment viewers, or users with access to applications in this environment can list clusters",
        )

    return service.get_clusters_by_environment(
        organization_id=ctx.organization.id,
        environment_uuid=environment_uuid,
        skip=skip,
        limit=limit,
    )


@router.delete("/{uuid}", response_model=dict)
def delete_cluster(
    organization_uuid: UUID,
    uuid: UUID,
    service: ClusterService = Depends(get_cluster_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Delete a cluster."""
    # Only org admins can delete clusters
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403, detail="Only organization admins can delete clusters"
        )

    try:
        return service.delete_cluster(uuid)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
