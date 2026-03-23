from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.webapps.infra.webapp_repository import WebappRepository
from app.webapps.core.webapp_service import WebappService
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.infra.environment_settings_repository import (
    EnvironmentSettingsRepository,
)
from app.environments.core.environment_service import EnvironmentService
from app.webapps.api.webapp_dto import (
    WebappCreate,
    WebappUpdate,
    Webapp,
    Pod,
    PodLogs,
    PodDescribe,
    PodCommandRequest,
    PodCommandResponse,
)
from app.webapps.core.webapp_validators import (
    WebappNotFoundError,
    WebappNotWebappTypeError,
    InstanceNotFoundError,
    InvalidExposureTypeError,
    InvalidVisibilityError,
    InvalidURLError,
    EnvironmentSettingsValidationError,
)

from app.webapps.core.webapp_pods_service import (
    get_webapp_pods_from_cluster,
    delete_webapp_pod_from_cluster,
    get_webapp_pod_logs_from_cluster,
    get_webapp_pod_describe_from_cluster,
    exec_webapp_pod_command_from_cluster,
)
from app.organizations.api.dependencies.organization_context import (
    getOrganizationContext,
)
from app.organizations.core.authorization import (
    OrganizationAccessContext,
    canViewApplication,
    canManageApplication,
    canViewEnvironment,
    isOrgMember,
    isEnvMaintainer,
    isEnvOperator,
    isAppDeveloper,
    isAppMaintainer,
)
from app.users.infra.user_model import User
from app.shared.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/organizations/{organization_uuid}/application_components/webapp",
    tags=["webapp"],
)


def get_webapp_service(database_session: Session = Depends(get_db)) -> WebappService:
    """Dependency to get WebappService instance."""
    webapp_repository = WebappRepository(database_session)
    settings_repository = EnvironmentSettingsRepository(database_session)
    return WebappService(webapp_repository, database_session, settings_repository)


def get_environment_service(
    database_session: Session = Depends(get_db),
) -> EnvironmentService:
    """Dependency to get EnvironmentService instance."""
    environment_repository = EnvironmentRepository(database_session)
    return EnvironmentService(environment_repository)


@router.post("/", response_model=Webapp)
def create_webapp(
    webapp: WebappCreate,
    service: WebappService = Depends(get_webapp_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Create a new webapp."""
    # Validate instance belongs to organization
    from app.instances.infra.instance_repository import InstanceRepository

    instance_repo = InstanceRepository(service.db)
    instance = instance_repo.find_by_uuid(webapp.instance_uuid)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if instance.application.organization_id != ctx.organization.id:
        raise HTTPException(
            status_code=403, detail="Instance does not belong to this organization"
        )

    if not canManageApplication(ctx, instance.application_id):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage applications"
        )

    try:
        return service.create_webapp(webapp)
    except (
        InstanceNotFoundError,
        InvalidExposureTypeError,
        InvalidVisibilityError,
        InvalidURLError,
        EnvironmentSettingsValidationError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Webapp])
def list_webapps(
    environment_uuid: UUID,
    skip: int = 0,
    limit: int = 100,
    service: WebappService = Depends(get_webapp_service),
    env_service: EnvironmentService = Depends(get_environment_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """List all webapps for the organization and environment."""
    try:
        environment_id = env_service.get_environment_id_for_organization(
            ctx.organization.id, environment_uuid
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not isOrgMember(ctx) and not canViewEnvironment(ctx, environment_id):
        raise HTTPException(
            status_code=403,
            detail="Only organization members or users with environment access can list webapps",
        )

    return service.get_webapps_by_environment(
        ctx.organization.id, environment_id, skip=skip, limit=limit
    )


@router.get("/{uuid}", response_model=Webapp)
def get_webapp(
    uuid: UUID,
    service: WebappService = Depends(get_webapp_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get webapp by UUID."""
    try:
        # Get raw model with relations for validation
        repository = WebappRepository(service.db)
        webapp_model = repository.find_by_uuid(uuid, load_relations=True)
        if not webapp_model:
            raise HTTPException(status_code=404, detail="Webapp not found")

        # Validate webapp belongs to organization; allow view by application or by environment
        if webapp_model.instance and webapp_model.instance.application:
            if webapp_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Webapp not found")
            if not canViewApplication(
                ctx, webapp_model.instance.application_id
            ) and not canViewEnvironment(ctx, webapp_model.instance.environment_id):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        return service.get_webapp(uuid)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{uuid}", response_model=Webapp)
def update_webapp(
    uuid: UUID,
    webapp: WebappUpdate,
    service: WebappService = Depends(get_webapp_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Update an existing webapp."""
    try:
        # Get raw model with relations for validation
        repository = WebappRepository(service.db)
        webapp_model = repository.find_by_uuid(uuid, load_relations=True)
        if not webapp_model:
            raise HTTPException(status_code=404, detail="Webapp not found")

        # Validate webapp belongs to organization; allow update by application or by env operator
        if webapp_model.instance and webapp_model.instance.application:
            if webapp_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Webapp not found")
            if (
                not canManageApplication(ctx, webapp_model.instance.application_id)
                and not isEnvOperator(ctx, webapp_model.instance.environment_id)
                and not isAppDeveloper(ctx, webapp_model.instance.application_id)
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        return service.update_webapp(uuid, webapp)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (
        InvalidURLError,
        InvalidExposureTypeError,
        InvalidVisibilityError,
        EnvironmentSettingsValidationError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{uuid}")
def delete_webapp(
    uuid: UUID,
    service: WebappService = Depends(get_webapp_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Delete a webapp."""
    try:
        # Get raw model with relations for validation
        repository = WebappRepository(service.db)
        webapp_model = repository.find_by_uuid(uuid, load_relations=True)
        if not webapp_model:
            raise HTTPException(status_code=404, detail="Webapp not found")

        # Validate webapp belongs to organization; allow delete by application or by env maintainer
        if webapp_model.instance and webapp_model.instance.application:
            if webapp_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Webapp not found")
            if (
                not canManageApplication(ctx, webapp_model.instance.application_id)
                and not isEnvMaintainer(ctx, webapp_model.instance.environment_id)
                and not isAppMaintainer(ctx, webapp_model.instance.application_id)
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        return service.delete_webapp(uuid)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{uuid}/secrets")
def get_webapp_secrets(
    uuid: UUID,
    service: WebappService = Depends(get_webapp_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """
    Get decrypted secrets for a webapp.
    Admin only endpoint - returns plaintext secret values.

    Security: This endpoint is protected by admin role requirement.
    All access is logged for audit purposes.
    """
    import logging
    from app.shared.crypto import decrypt_secret

    logger = logging.getLogger(__name__)

    try:
        webapp = service.get_webapp_raw(uuid)
        if not webapp:
            raise HTTPException(status_code=404, detail="Webapp not found")
        # Validate webapp belongs to organization
        if webapp.instance and webapp.instance.application:
            if webapp.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Webapp not found")
            if not canManageApplication(ctx, webapp.instance.application_id):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Audit log: Admin accessing secrets
        logger.info(
            f"SECURITY_AUDIT: Admin '{current_user.email}' accessed secrets "
            f"for webapp '{webapp.name}' (uuid: {uuid})"
        )

        settings = webapp.settings or {}
        encrypted_secrets = settings.get("secrets", [])

        decrypted_secrets = []
        for secret in encrypted_secrets:
            try:
                decrypted_value = decrypt_secret(secret.get("value", ""))
                decrypted_secrets.append(
                    {"key": secret.get("key", ""), "value": decrypted_value}
                )
            except Exception as e:
                # Log decryption failure (could indicate key rotation issue)
                logger.warning(
                    f"SECURITY_AUDIT: Failed to decrypt secret '{secret.get('key')}' "
                    f"for webapp {uuid}: {type(e).__name__}"
                )
                decrypted_secrets.append(
                    {"key": secret.get("key", ""), "value": "********"}
                )

        return {"secrets": decrypted_secrets}
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{uuid}/pods", response_model=list[Pod])
def get_webapp_pods(
    uuid: UUID,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get pods for a webapp."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    # Validate webapp belongs to organization; allow view by application or by environment
    if webapp.instance and webapp.instance.application:
        if webapp.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if not canViewApplication(
            ctx, webapp.instance.application_id
        ) and not canViewEnvironment(ctx, webapp.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Webapp is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    # Use namespace from database (supports both legacy and new apps)
    application = webapp.instance.application
    namespace = application.namespace if application.namespace else application.name
    component_name = webapp.name

    try:
        pods = get_webapp_pods_from_cluster(cluster, namespace, component_name)
        return pods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pods: {str(e)}")


@router.delete("/{uuid}/pods/{pod_name}")
def delete_webapp_pod(
    uuid: UUID,
    pod_name: str,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Delete a pod for a webapp."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    # Validate webapp belongs to organization; allow delete by application or by env maintainer
    if webapp.instance and webapp.instance.application:
        if webapp.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if (
            not canManageApplication(ctx, webapp.instance.application_id)
            and not isEnvMaintainer(ctx, webapp.instance.environment_id)
            and not isAppMaintainer(ctx, webapp.instance.application_id)
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Webapp is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    # Use namespace from database (supports both legacy and new apps)
    application = webapp.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        delete_webapp_pod_from_cluster(cluster, namespace, pod_name)
        return {"detail": f"Pod {pod_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete pod {pod_name}: {str(e)}"
        )


@router.get("/{uuid}/pods/{pod_name}/logs", response_model=PodLogs)
def get_webapp_pod_logs(
    uuid: UUID,
    pod_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get logs for a pod."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    # Validate webapp belongs to organization; allow view by application or by environment
    if webapp.instance and webapp.instance.application:
        if webapp.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if not canViewApplication(
            ctx, webapp.instance.application_id
        ) and not canViewEnvironment(ctx, webapp.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Webapp is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    # Use namespace from database (supports both legacy and new apps)
    application = webapp.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        logs = get_webapp_pod_logs_from_cluster(
            cluster, namespace, pod_name, container_name, tail_lines
        )
        return {"logs": logs, "pod_name": pod_name, "container_name": container_name}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get logs for pod {pod_name}: {str(e)}"
        )


@router.get("/{uuid}/pods/{pod_name}/describe", response_model=PodDescribe)
def get_webapp_pod_describe(
    uuid: UUID,
    pod_name: str,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get pod description (same output as kubectl describe pod)."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    if webapp.instance and webapp.instance.application:
        if webapp.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if not canViewApplication(
            ctx, webapp.instance.application_id
        ) and not canViewEnvironment(ctx, webapp.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Webapp is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = webapp.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        describe = get_webapp_pod_describe_from_cluster(cluster, namespace, pod_name)
        return {"describe": describe, "pod_name": pod_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get describe for pod {pod_name}: {str(e)}",
        )


@router.post("/{uuid}/pods/{pod_name}/exec", response_model=PodCommandResponse)
def exec_webapp_pod_command(
    http_request: Request,
    uuid: UUID,
    pod_name: str,
    request: PodCommandRequest,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Execute a command in a pod."""
    http_request.state.audit_exec_payload = {
        "request": {
            "command": request.command,
            "container_name": request.container_name,
        }
    }
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    # Validate webapp belongs to organization
    if webapp.instance and webapp.instance.application:
        if webapp.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if not canManageApplication(ctx, webapp.instance.application_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Webapp is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    # Use namespace from database (supports both legacy and new apps)
    application = webapp.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        result = exec_webapp_pod_command_from_cluster(
            cluster, namespace, pod_name, request.command, request.container_name
        )
        http_request.state.audit_exec_payload["response"] = {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "return_code": result.get("return_code", -1),
        }
        return result
    except Exception as e:
        http_request.state.audit_exec_payload["response"] = {"error": str(e)}
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute command in pod {pod_name}: {str(e)}",
        )
