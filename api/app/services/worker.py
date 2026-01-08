from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4
from uuid import UUID

import app.models.application_components as ApplicationComponentModel
import app.models.instance as InstanceModel
import app.models.cluster_instance as ClusterInstanceModel
import app.models.settings as SettingsModel
import app.schemas.worker as WorkerSchema
from app.helpers.serializers import serialize_application_component, serialize_settings
from app.k8s.client import K8sClient
from app.services.kubernetes.application_component_manager import (
    KubernetesApplicationComponentManager,
)
from app.services.cluster_selection import ClusterSelectionService
from app.services.cluster import get_gateway_reference_from_cluster


class WorkerService:
    @staticmethod
    def upsert_worker(
        db: Session,
        worker: WorkerSchema.WorkerCreate | WorkerSchema.WorkerUpdate,
        uuid: UUID = None,
    ):
        if uuid:
            # Update existing worker
            db_worker = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
                .first()
            )

            if db_worker is None:
                raise HTTPException(status_code=404, detail="Worker not found")

            if db_worker.type != ApplicationComponentModel.WebappType.worker:
                raise HTTPException(
                    status_code=400,
                    detail="Component is not a worker"
                )

            # Cast to WorkerUpdate for type checking
            worker_update = WorkerSchema.WorkerUpdate.model_validate(worker)

            # Verificar se houve mudança no enabled
            enabled_changed = worker_update.enabled is not None and worker_update.enabled != db_worker.enabled
            was_enabled = db_worker.enabled
            will_be_enabled = worker_update.enabled if worker_update.enabled is not None else db_worker.enabled

            if worker_update.enabled is not None:
                db_worker.enabled = worker_update.enabled
            if worker_update.settings is not None:
                db_worker.settings = worker_update.settings.model_dump()

            # Buscar o cluster_instance relacionado ao componente
            cluster_instance = (
                db.query(ClusterInstanceModel.ClusterInstance)
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_worker.id)
                .first()
            )

            # Se não existir, criar automaticamente usando o cluster de menor carga
            if cluster_instance is None:
                instance = db_worker.instance
                cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                    db, instance.environment_id, instance.environment.name
                )

                # Criar novo cluster_instance
                cluster_instance = ClusterInstanceModel.ClusterInstance(
                    uuid=uuid4(),
                    cluster_id=cluster.id,
                    application_component_id=db_worker.id,
                )
                db.add(cluster_instance)
            else:
                cluster = cluster_instance.cluster

            # Buscar settings do environment
            instance = db_worker.instance
            settings = (
                db.query(SettingsModel.Settings)
                .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                .all()
            )
            settings_serialized = serialize_settings(settings)

            # Recarregar o componente com relacionamentos para serialização usando joinedload
            db_worker = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_worker.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_worker)
            component_type = db_worker.type.value if hasattr(db_worker.type, 'value') else str(db_worker.type)

            # Se o componente foi desativado (enabled mudou de True para False), remover do Kubernetes
            if enabled_changed and was_enabled and not will_be_enabled:
                try:
                    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
                    application_name = application_component_serialized.get("application_name")
                    if application_name:
                        k8s_client.ensure_namespace_exists(application_name)

                    gateway_reference = get_gateway_reference_from_cluster(cluster)
                    kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                        application_component_serialized, component_type, settings_serialized, db=db,
                        gateway_reference=gateway_reference
                    )
                    k8s_client.apply_or_delete_yaml_to_k8s(
                        kubernetes_payload, operation="delete"
                    )

                    db.commit()
                    db.refresh(db_worker)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    # Log do erro mas continua com a atualização do banco
                    print(f"Error removing component '{db_worker.name}' from Kubernetes: {e}")
                    db.commit()
                    db.refresh(db_worker)
                    if cluster_instance:
                        db.refresh(cluster_instance)

            # Se o componente foi reativado (enabled mudou de False para True), reaplicar no Kubernetes
            elif enabled_changed and not was_enabled and will_be_enabled:
                try:
                    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
                    application_name = application_component_serialized.get("application_name")
                    if application_name:
                        k8s_client.ensure_namespace_exists(application_name)

                    gateway_reference = get_gateway_reference_from_cluster(cluster)
                    kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                        application_component_serialized, component_type, settings_serialized, db=db,
                        gateway_reference=gateway_reference
                    )
                    k8s_client.apply_or_delete_yaml_to_k8s(
                        kubernetes_payload, operation="upsert"
                    )

                    db.commit()
                    db.refresh(db_worker)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to reapply component to Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

            # Se não houve mudança no enabled ou se está habilitado, aplicar normalmente
            elif not enabled_changed or db_worker.enabled:
                try:
                    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

                    # Verificar e criar namespace com o nome da aplicação se não existir
                    application_name = application_component_serialized.get("application_name")
                    if application_name:
                        k8s_client.ensure_namespace_exists(application_name)

                    gateway_reference = get_gateway_reference_from_cluster(cluster)
                    kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                        application_component_serialized, component_type, settings_serialized, db=db,
                        gateway_reference=gateway_reference
                    )
                    k8s_client.apply_or_delete_yaml_to_k8s(
                        kubernetes_payload, operation="upsert"
                    )

                    db.commit()
                    db.refresh(db_worker)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to update component in Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

        else:
            # Create new worker
            worker_create = WorkerSchema.WorkerCreate.model_validate(worker)

            # Buscar a instância
            instance = (
                db.query(InstanceModel.Instance)
                .filter(InstanceModel.Instance.uuid == worker_create.instance_uuid)
                .first()
            )

            if instance is None:
                raise HTTPException(status_code=404, detail="Instance not found")

            # Garantir que settings tenha exposure com visibility private
            settings_dict = worker_create.settings.model_dump()
            if 'exposure' not in settings_dict:
                settings_dict['exposure'] = {
                    'type': 'http',
                    'port': 80,
                    'visibility': 'private'
                }
            elif 'visibility' not in settings_dict.get('exposure', {}):
                settings_dict['exposure']['visibility'] = 'private'

            db_worker = ApplicationComponentModel.ApplicationComponent(
                uuid=uuid4(),
                instance_id=instance.id,
                name=worker_create.name,
                type=ApplicationComponentModel.WebappType.worker,
                settings=settings_dict,
                url=None,  # Worker components don't have URLs
                enabled=worker_create.enabled,
            )
            db.add(db_worker)

            try:
                db.commit()
                db.refresh(db_worker)
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"{e._sql_message}"}
                raise HTTPException(status_code=400, detail=message)

            # Criar cluster_instance automaticamente usando o cluster de menor carga
            cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                db, instance.environment_id, instance.environment.name
            )

            # Verificar se já existe um cluster_instance para este componente (não deveria acontecer em criação)
            existing_cluster_instance = (
                db.query(ClusterInstanceModel.ClusterInstance)
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_worker.id)
                .first()
            )

            if existing_cluster_instance:
                # Se já existe, usar o cluster existente (caso de race condition ou erro anterior)
                cluster_instance = existing_cluster_instance
                cluster = cluster_instance.cluster
            else:
                # Criar novo cluster_instance
                cluster_instance = ClusterInstanceModel.ClusterInstance(
                    uuid=uuid4(),
                    cluster_id=cluster.id,
                    application_component_id=db_worker.id,
                )
                db.add(cluster_instance)

            # Buscar settings do environment
            settings = (
                db.query(SettingsModel.Settings)
                .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                .all()
            )
            settings_serialized = serialize_settings(settings)

            # Recarregar o componente com relacionamentos para serialização usando joinedload
            db_worker = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_worker.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_worker)
            component_type = db_worker.type.value if hasattr(db_worker.type, 'value') else str(db_worker.type)

            # Aplicar recursos no Kubernetes
            try:
                k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

                # Verificar e criar namespace com o nome da aplicação se não existir
                application_name = application_component_serialized.get("application_name")
                if application_name:
                    k8s_client.ensure_namespace_exists(application_name)

                kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                    application_component_serialized, component_type, settings_serialized, db=db
                )
                k8s_client.apply_or_delete_yaml_to_k8s(
                    kubernetes_payload, operation="create"
                )

                # Commit do cluster_instance e do componente
                db.commit()
                db.refresh(cluster_instance)
                db.refresh(db_worker)
            except Exception as e:
                db.rollback()
                # Se falhar ao aplicar no Kubernetes, removemos o componente criado
                # para manter a consistência
                db.delete(db_worker)
                if not existing_cluster_instance:
                    # Se criamos um cluster_instance, removemos também
                    if cluster_instance in db:
                        db.delete(cluster_instance)
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to deploy component to Kubernetes cluster '{cluster.name}': {str(e)}"
                )

        return db_worker

    @staticmethod
    def get_worker(
        db: Session, uuid: UUID
    ) -> WorkerSchema.Worker:
        db_worker = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )
        if db_worker is None:
            raise HTTPException(status_code=404, detail="Worker not found")
        if db_worker.type != ApplicationComponentModel.WebappType.worker:
            raise HTTPException(
                status_code=400,
                detail="Component is not a worker"
            )
        return WorkerSchema.Worker.model_validate(db_worker)

    @staticmethod
    def get_workers(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[WorkerSchema.Worker]:
        db_workers = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.worker)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [WorkerSchema.Worker.model_validate(worker) for worker in db_workers]

    @staticmethod
    def delete_worker(db: Session, uuid: UUID):
        # Buscar o componente com relacionamentos
        db_worker = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .options(
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.application),
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.environment),
                joinedload(ApplicationComponentModel.ApplicationComponent.instances)
            )
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )

        if db_worker is None:
            raise HTTPException(status_code=404, detail="Worker not found")
        if db_worker.type != ApplicationComponentModel.WebappType.worker:
            raise HTTPException(
                status_code=400,
                detail="Component is not a worker"
            )

        # Buscar o cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_worker.id)
            .first()
        )

        # Se existir cluster_instance, deletar os recursos no Kubernetes
        if cluster_instance:
            try:
                cluster = cluster_instance.cluster

                # Buscar settings do environment
                instance = db_worker.instance
                settings = (
                    db.query(SettingsModel.Settings)
                    .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                    .all()
                )
                settings_serialized = serialize_settings(settings)

                # Recarregar o componente com relacionamentos para serialização
                db_worker = (
                    db.query(ApplicationComponentModel.ApplicationComponent)
                    .options(
                        joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                        .joinedload(InstanceModel.Instance.application),
                        joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                        .joinedload(InstanceModel.Instance.environment)
                    )
                    .filter(ApplicationComponentModel.ApplicationComponent.id == db_worker.id)
                    .first()
                )

                # Serializar o componente para os templates
                application_component_serialized = serialize_application_component(db_worker)
                component_type = db_worker.type.value if hasattr(db_worker.type, 'value') else str(db_worker.type)

                # Criar cliente Kubernetes
                k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

                # Deletar recursos do Kubernetes
                kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                    application_component_serialized, component_type, settings_serialized, db=db
                )
                k8s_client.apply_or_delete_yaml_to_k8s(
                    kubernetes_payload, operation="delete"
                )
            except Exception as e:
                # Se falhar ao deletar do Kubernetes, logamos o erro mas continuamos
                # para deletar do banco de dados (pode ser que o recurso já não exista)
                # mas logamos o erro
                print(f"Error deleting resources from Kubernetes: {e}")

        # Deletar o cluster_instance e o componente do banco
        try:
            if cluster_instance:
                db.delete(cluster_instance)
            db.delete(db_worker)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e._sql_message}"}
            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Worker deleted successfully"}

