from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.workers.infra.worker_repository import WorkerRepository
from app.workers.core.worker_service import WorkerService
from app.environments.infra.environment_settings_repository import (
    EnvironmentSettingsRepository,
)
from app.workers.api.worker_dto import (
    WorkerCreate,
    WorkerUpdate,
    Worker,
    Pod,
    PodLogs,
    PodDescribe,
    PodCommandRequest,
    PodCommandResponse,
)
from app.workers.core.worker_pods_service import (
    get_worker_pods_from_cluster,
    delete_worker_pod_from_cluster,
    get_worker_pod_logs_from_cluster,
    get_worker_pod_describe_from_cluster,
    exec_worker_pod_command_from_cluster,
)
from app.workers.core.worker_validators import (
    WorkerNotFoundError,
    WorkerNotWorkerTypeError,
    InstanceNotFoundError,
)
from app.webapps.core.webapp_validators import EnvironmentSettingsValidationError
from app.users.infra.user_model import UserRole, User
from app.shared.dependencies.auth import require_role, get_current_user
from app.organizations.api.dependencies.organization_context import (
    getOrganizationContext,
)
from app.organizations.core.authorization import (
    OrganizationAccessContext,
    canViewApplication,
    canManageApplication,
    canViewEnvironment,
    isEnvMaintainer,
    isEnvOperator,
    isAppDeveloper,
    isAppMaintainer,
)


router = APIRouter(
    prefix="/organizations/{organization_uuid}/application_components/worker",
    tags=["worker"],
)


def get_worker_service(database_session: Session = Depends(get_db)) -> WorkerService:
    """Dependency to get WorkerService instance."""
    worker_repository = WorkerRepository(database_session)
    settings_repository = EnvironmentSettingsRepository(database_session)
    return WorkerService(worker_repository, database_session, settings_repository)


@router.post("/", response_model=Worker)
def create_worker(
    organization_uuid: UUID,
    worker: WorkerCreate,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Create a new worker."""
    # Validate instance belongs to organization; allow create by application or by env maintainer
    from app.instances.infra.instance_repository import InstanceRepository

    instance_repo = InstanceRepository(service.db)
    instance = instance_repo.find_by_uuid(worker.instance_uuid)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if instance.application.organization_id != ctx.organization.id:
        raise HTTPException(
            status_code=403, detail="Instance does not belong to this organization"
        )

    if (
        not canManageApplication(ctx, instance.application_id)
        and not isEnvMaintainer(ctx, instance.environment_id)
        and not isAppMaintainer(ctx, instance.application_id)
    ):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage applications"
        )

    try:
        return service.create_worker(worker)
    except (InstanceNotFoundError, EnvironmentSettingsValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Worker])
def list_workers(
    organization_uuid: UUID,
    skip: int = 0,
    limit: int = 100,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """List all workers for the organization."""
    # Get workers filtered by organization
    return service.get_workers_by_organization(
        ctx.organization.id, skip=skip, limit=limit
    )


@router.get("/{uuid}", response_model=Worker)
def get_worker(
    organization_uuid: UUID,
    uuid: UUID,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get worker by UUID."""
    try:
        repository = WorkerRepository(service.db)
        worker_model = repository.find_by_uuid(uuid, load_relations=True)
        if not worker_model or worker_model.type.value != "worker":
            raise HTTPException(status_code=404, detail="Worker not found")
        # Validate worker belongs to organization; allow view by application or by environment
        if worker_model.instance and worker_model.instance.application:
            if worker_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Worker not found")
            if not canViewApplication(
                ctx, worker_model.instance.application_id
            ) and not canViewEnvironment(ctx, worker_model.instance.environment_id):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return service.get_worker(uuid)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{uuid}", response_model=Worker)
def update_worker(
    organization_uuid: UUID,
    uuid: UUID,
    worker: WorkerUpdate,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Update an existing worker."""
    try:
        repository = WorkerRepository(service.db)
        worker_model = repository.find_by_uuid(uuid, load_relations=True)
        if not worker_model or worker_model.type.value != "worker":
            raise HTTPException(status_code=404, detail="Worker not found")
        # Validate worker belongs to organization; allow update by application or by env operator
        if worker_model.instance and worker_model.instance.application:
            if worker_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Worker not found")
            if (
                not canManageApplication(ctx, worker_model.instance.application_id)
                and not isEnvOperator(ctx, worker_model.instance.environment_id)
                and not isAppDeveloper(ctx, worker_model.instance.application_id)
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return service.update_worker(uuid, worker)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EnvironmentSettingsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{uuid}")
def delete_worker(
    organization_uuid: UUID,
    uuid: UUID,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Delete a worker."""
    try:
        repository = WorkerRepository(service.db)
        worker_model = repository.find_by_uuid(uuid, load_relations=True)
        if not worker_model or worker_model.type.value != "worker":
            raise HTTPException(status_code=404, detail="Worker not found")
        # Validate worker belongs to organization; allow delete by application or by env maintainer
        if worker_model.instance and worker_model.instance.application:
            if worker_model.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Worker not found")
            if (
                not canManageApplication(ctx, worker_model.instance.application_id)
                and not isEnvMaintainer(ctx, worker_model.instance.environment_id)
                and not isAppMaintainer(ctx, worker_model.instance.application_id)
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return service.delete_worker(uuid)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{uuid}/secrets")
def get_worker_secrets(
    organization_uuid: UUID,
    uuid: UUID,
    service: WorkerService = Depends(get_worker_service),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """
    Get decrypted secrets for a worker.
    Admin only endpoint - returns plaintext secret values.

    Security: This endpoint is protected by admin role requirement.
    All access is logged for audit purposes.
    """
    import logging
    from app.shared.crypto import decrypt_secret

    logger = logging.getLogger(__name__)

    try:
        repository = WorkerRepository(service.db)
        worker = repository.find_by_uuid(uuid, load_relations=True)
        if not worker or worker.type.value != "worker":
            raise HTTPException(status_code=404, detail="Worker not found")
        # Validate worker belongs to organization
        if worker.instance and worker.instance.application:
            if worker.instance.application.organization_id != ctx.organization.id:
                raise HTTPException(status_code=404, detail="Worker not found")
            if not canManageApplication(ctx, worker.instance.application_id):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Audit log: Admin accessing secrets
        logger.info(
            f"SECURITY_AUDIT: Admin '{current_user.email}' accessed secrets "
            f"for worker '{worker.name}' (uuid: {uuid})"
        )

        settings = worker.settings or {}
        encrypted_secrets = settings.get("secrets", [])

        decrypted_secrets = []
        for secret in encrypted_secrets:
            try:
                decrypted_value = decrypt_secret(secret.get("value", ""))
                decrypted_secrets.append(
                    {"key": secret.get("key", ""), "value": decrypted_value}
                )
            except Exception as e:
                logger.warning(
                    f"SECURITY_AUDIT: Failed to decrypt secret '{secret.get('key')}' "
                    f"for worker {uuid}: {type(e).__name__}"
                )
                decrypted_secrets.append(
                    {"key": secret.get("key", ""), "value": "********"}
                )

        return {"secrets": decrypted_secrets}
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{uuid}/pods", response_model=list[Pod])
def get_worker_pods(
    uuid: UUID,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get pods for a worker."""
    repository = WorkerRepository(database_session)
    worker = repository.find_by_uuid(uuid, load_relations=True)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker.type.value != "worker":
        raise HTTPException(status_code=400, detail="Component is not a worker")

    # Validate worker belongs to organization; allow view by application or by environment
    if worker.instance and worker.instance.application:
        if worker.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Worker not found")
        if not canViewApplication(
            ctx, worker.instance.application_id
        ) and not canViewEnvironment(ctx, worker.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(worker.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Worker is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = worker.instance.application
    namespace = application.namespace if application.namespace else application.name
    component_name = worker.name

    try:
        pods = get_worker_pods_from_cluster(cluster, namespace, component_name)
        return pods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pods: {str(e)}")


@router.delete("/{uuid}/pods/{pod_name}")
def delete_worker_pod(
    uuid: UUID,
    pod_name: str,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Delete a pod for a worker."""
    repository = WorkerRepository(database_session)
    worker = repository.find_by_uuid(uuid, load_relations=True)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker.type.value != "worker":
        raise HTTPException(status_code=400, detail="Component is not a worker")

    # Validate worker belongs to organization; allow delete by application or by env maintainer
    if worker.instance and worker.instance.application:
        if worker.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Worker not found")
        if (
            not canManageApplication(ctx, worker.instance.application_id)
            and not isEnvMaintainer(ctx, worker.instance.environment_id)
            and not isAppMaintainer(ctx, worker.instance.application_id)
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(worker.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Worker is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = worker.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        delete_worker_pod_from_cluster(cluster, namespace, pod_name)
        return {"detail": f"Pod {pod_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete pod {pod_name}: {str(e)}"
        )


@router.get("/{uuid}/pods/{pod_name}/logs", response_model=PodLogs)
def get_worker_pod_logs(
    uuid: UUID,
    pod_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get logs for a pod."""
    repository = WorkerRepository(database_session)
    worker = repository.find_by_uuid(uuid, load_relations=True)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker.type.value != "worker":
        raise HTTPException(status_code=400, detail="Component is not a worker")

    # Validate worker belongs to organization; allow view by application or by environment
    if worker.instance and worker.instance.application:
        if worker.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Worker not found")
        if not canViewApplication(
            ctx, worker.instance.application_id
        ) and not canViewEnvironment(ctx, worker.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(worker.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Worker is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = worker.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        logs = get_worker_pod_logs_from_cluster(
            cluster, namespace, pod_name, container_name, tail_lines
        )
        return {"logs": logs, "pod_name": pod_name, "container_name": container_name}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get logs for pod {pod_name}: {str(e)}"
        )


@router.get("/{uuid}/pods/{pod_name}/describe", response_model=PodDescribe)
def get_worker_pod_describe(
    uuid: UUID,
    pod_name: str,
    database_session: Session = Depends(get_db),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
    current_user: User = Depends(get_current_user),
):
    """Get pod description (same output as kubectl describe pod)."""
    repository = WorkerRepository(database_session)
    worker = repository.find_by_uuid(uuid, load_relations=True)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker.type.value != "worker":
        raise HTTPException(status_code=400, detail="Component is not a worker")

    if worker.instance and worker.instance.application:
        if worker.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Worker not found")
        if not canViewApplication(
            ctx, worker.instance.application_id
        ) and not canViewEnvironment(ctx, worker.instance.environment_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(worker.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Worker is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = worker.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        describe = get_worker_pod_describe_from_cluster(cluster, namespace, pod_name)
        return {"describe": describe, "pod_name": pod_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get describe for pod {pod_name}: {str(e)}",
        )


@router.post("/{uuid}/pods/{pod_name}/exec", response_model=PodCommandResponse)
def exec_worker_pod_command(
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
    repository = WorkerRepository(database_session)
    worker = repository.find_by_uuid(uuid, load_relations=True)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker.type.value != "worker":
        raise HTTPException(status_code=400, detail="Component is not a worker")

    # Validate worker belongs to organization; allow exec by application or by env maintainer
    if worker.instance and worker.instance.application:
        if worker.instance.application.organization_id != ctx.organization.id:
            raise HTTPException(status_code=404, detail="Worker not found")
        if (
            not canManageApplication(ctx, worker.instance.application_id)
            and not isEnvMaintainer(ctx, worker.instance.environment_id)
            and not isAppMaintainer(ctx, worker.instance.application_id)
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    cluster_instance = repository.find_cluster_instance_by_component_id(worker.id)
    if not cluster_instance:
        raise HTTPException(
            status_code=404, detail="Worker is not deployed to any cluster"
        )

    cluster = cluster_instance.cluster
    application = worker.instance.application
    namespace = application.namespace if application.namespace else application.name

    try:
        result = exec_worker_pod_command_from_cluster(
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
