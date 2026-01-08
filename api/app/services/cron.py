from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4
from uuid import UUID

import app.models.application_components as ApplicationComponentModel
import app.models.instance as InstanceModel
import app.models.cluster_instance as ClusterInstanceModel
import app.models.settings as SettingsModel
import app.schemas.cron as CronSchema
from app.helpers.serializers import serialize_application_component, serialize_settings
from app.k8s.client import K8sClient
from app.services.kubernetes.application_component_manager import (
    KubernetesApplicationComponentManager,
)
from app.services.cluster_selection import ClusterSelectionService
from app.services.cluster import get_gateway_reference_from_cluster


class CronService:
    @staticmethod
    def upsert_cron(
        db: Session,
        cron: CronSchema.CronCreate | CronSchema.CronUpdate,
        uuid: UUID = None,
    ):
        if uuid:
            # Update existing cron
            db_cron = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
                .first()
            )

            if db_cron is None:
                raise HTTPException(status_code=404, detail="Cron not found")

            if db_cron.type != ApplicationComponentModel.WebappType.cron:
                raise HTTPException(
                    status_code=400,
                    detail="Component is not a cron"
                )

            # Cast to CronUpdate for type checking
            cron_update = CronSchema.CronUpdate.model_validate(cron)

            # Verificar se houve mudança no enabled
            enabled_changed = cron_update.enabled is not None and cron_update.enabled != db_cron.enabled
            was_enabled = db_cron.enabled
            will_be_enabled = cron_update.enabled if cron_update.enabled is not None else db_cron.enabled

            if cron_update.enabled is not None:
                db_cron.enabled = cron_update.enabled
            if cron_update.settings is not None:
                db_cron.settings = cron_update.settings.model_dump()

            # Buscar o cluster_instance relacionado ao componente
            cluster_instance = (
                db.query(ClusterInstanceModel.ClusterInstance)
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
                .first()
            )

            # Se não existir, criar automaticamente usando o cluster de menor carga
            if cluster_instance is None:
                instance = db_cron.instance
                cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                    db, instance.environment_id, instance.environment.name
                )

                # Criar novo cluster_instance
                cluster_instance = ClusterInstanceModel.ClusterInstance(
                    uuid=uuid4(),
                    cluster_id=cluster.id,
                    application_component_id=db_cron.id,
                )
                db.add(cluster_instance)
            else:
                cluster = cluster_instance.cluster

            # Buscar settings do environment
            instance = db_cron.instance
            settings = (
                db.query(SettingsModel.Settings)
                .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                .all()
            )
            settings_serialized = serialize_settings(settings)

            # Recarregar o componente com relacionamentos para serialização usando joinedload
            db_cron = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_cron.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_cron)
            component_type = db_cron.type.value if hasattr(db_cron.type, 'value') else str(db_cron.type)

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
                    db.refresh(db_cron)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    # Log do erro mas continua com a atualização do banco
                    print(f"Error removing component '{db_cron.name}' from Kubernetes: {e}")
                    db.commit()
                    db.refresh(db_cron)
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
                    db.refresh(db_cron)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to reapply component to Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

            # Se não houve mudança no enabled ou se está habilitado, aplicar normalmente
            elif not enabled_changed or db_cron.enabled:
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
                    db.refresh(db_cron)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to update component in Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

        else:
            # Create new cron
            # Cast to CronCreate for type checking
            cron_create = CronSchema.CronCreate.model_validate(cron)

            # Get instance by uuid
            instance = (
                db.query(InstanceModel.Instance)
                .filter(InstanceModel.Instance.uuid == cron_create.instance_uuid)
                .first()
            )
            if instance is None:
                raise HTTPException(status_code=404, detail="Instance not found")

            # Garantir que settings tenha exposure com visibility private
            settings_dict = cron_create.settings.model_dump()
            if 'exposure' not in settings_dict:
                settings_dict['exposure'] = {
                    'type': 'http',
                    'port': 80,
                    'visibility': 'private'
                }
            elif 'visibility' not in settings_dict.get('exposure', {}):
                settings_dict['exposure']['visibility'] = 'private'

            db_cron = ApplicationComponentModel.ApplicationComponent(
                uuid=uuid4(),
                instance_id=instance.id,
                name=cron_create.name,
                type=ApplicationComponentModel.WebappType.cron,
                settings=settings_dict,
                url=None,  # Cron components don't have URLs
                enabled=cron_create.enabled,
            )
            db.add(db_cron)

            try:
                db.commit()
                db.refresh(db_cron)
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
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
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
                    application_component_id=db_cron.id,
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
            db_cron = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_cron.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_cron)
            component_type = db_cron.type.value if hasattr(db_cron.type, 'value') else str(db_cron.type)

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
                db.refresh(db_cron)
            except Exception as e:
                db.rollback()
                # Se falhar ao aplicar no Kubernetes, removemos o componente criado
                # para manter a consistência
                db.delete(db_cron)
                if not existing_cluster_instance:
                    # Se criamos um cluster_instance, removemos também
                    if cluster_instance in db:
                        db.delete(cluster_instance)
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to deploy component to Kubernetes cluster '{cluster.name}': {str(e)}"
                )

        return db_cron

    @staticmethod
    def get_cron(
        db: Session, uuid: UUID
    ) -> CronSchema.Cron:
        db_cron = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )
        if db_cron is None:
            raise HTTPException(status_code=404, detail="Cron not found")
        if db_cron.type != ApplicationComponentModel.WebappType.cron:
            raise HTTPException(
                status_code=400,
                detail="Component is not a cron"
            )
        return CronSchema.Cron.model_validate(db_cron)

    @staticmethod
    def get_crons(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[CronSchema.Cron]:
        db_crons = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.cron)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [CronSchema.Cron.model_validate(cron) for cron in db_crons]

    @staticmethod
    def get_cron_jobs(db: Session, uuid: UUID):
        """
        Lista os Jobs executados por um CronJob específico.
        """
        # Buscar o componente com relacionamentos
        db_cron = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .options(
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.application),
                joinedload(ApplicationComponentModel.ApplicationComponent.instances)
                .joinedload(ClusterInstanceModel.ClusterInstance.cluster)
            )
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )

        if db_cron is None:
            raise HTTPException(status_code=404, detail="Cron not found")
        if db_cron.type != ApplicationComponentModel.WebappType.cron:
            raise HTTPException(
                status_code=400,
                detail="Component is not a cron"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Cron is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_cron.instance.application.name
        component_name = db_cron.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Listar jobs usando label selector baseado no nome do componente
        # Jobs criados por CronJobs têm labels que incluem o nome do CronJob
        label_selector = f"app={component_name}"
        jobs = k8s_client.list_jobs(namespace=application_name, label_selector=label_selector)

        # Se não encontrar com esse seletor, tentar sem seletor e filtrar depois
        if not jobs:
            all_jobs = k8s_client.list_jobs(namespace=application_name)
            jobs = [job for job in all_jobs if component_name in job['name']]

        return jobs

    @staticmethod
    def get_cron_job_logs(db: Session, uuid: UUID, job_name: str, container_name: str = None, tail_lines: int = 100):
        """
        Obtém os logs dos pods criados por um Job específico de um CronJob.
        """
        # Buscar o componente com relacionamentos
        db_cron = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .options(
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.application),
                joinedload(ApplicationComponentModel.ApplicationComponent.instances)
                .joinedload(ClusterInstanceModel.ClusterInstance.cluster)
            )
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )

        if db_cron is None:
            raise HTTPException(status_code=404, detail="Cron not found")
        if db_cron.type != ApplicationComponentModel.WebappType.cron:
            raise HTTPException(
                status_code=400,
                detail="Component is not a cron"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Cron is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_cron.instance.application.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Buscar pods do Job usando label selector job-name
        # Jobs criam pods com label job-name=<job-name>
        label_selector = f"job-name={job_name}"
        pods = k8s_client.list_pods(namespace=application_name, label_selector=label_selector)

        if not pods:
            raise HTTPException(
                status_code=404,
                detail=f"No pods found for job {job_name}"
            )

        # Pegar o primeiro pod (geralmente Jobs criam apenas um pod)
        pod_name = pods[0]['name']

        # Obter logs do pod
        try:
            logs = k8s_client.get_pod_logs(
                namespace=application_name,
                pod_name=pod_name,
                container_name=container_name,
                tail_lines=tail_lines
            )
            return {"logs": logs, "pod_name": pod_name, "job_name": job_name, "container_name": container_name}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get logs for job {job_name}: {str(e)}"
            )

    @staticmethod
    def delete_cron_job(db: Session, uuid: UUID, job_name: str):
        """
        Deleta um Job específico criado por um CronJob no Kubernetes.
        """
        # Buscar o componente com relacionamentos
        db_cron = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .options(
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.application),
                joinedload(ApplicationComponentModel.ApplicationComponent.instances)
                .joinedload(ClusterInstanceModel.ClusterInstance.cluster)
            )
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )

        if db_cron is None:
            raise HTTPException(status_code=404, detail="Cron not found")
        if db_cron.type != ApplicationComponentModel.WebappType.cron:
            raise HTTPException(
                status_code=400,
                detail="Component is not a cron"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Cron is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_cron.instance.application.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Deletar o job
        k8s_client.delete_job(namespace=application_name, job_name=job_name)

        return {"detail": f"Job '{job_name}' deleted successfully"}

    @staticmethod
    def delete_cron(db: Session, uuid: UUID):
        # Buscar o componente com relacionamentos
        db_cron = (
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

        if db_cron is None:
            raise HTTPException(status_code=404, detail="Cron not found")
        if db_cron.type != ApplicationComponentModel.WebappType.cron:
            raise HTTPException(
                status_code=400,
                detail="Component is not a cron"
            )

        # Buscar o cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_cron.id)
            .first()
        )

        # Se existir cluster_instance, deletar os recursos no Kubernetes
        if cluster_instance:
            try:
                cluster = cluster_instance.cluster

                # Buscar settings do environment
                instance = db_cron.instance
                settings = (
                    db.query(SettingsModel.Settings)
                    .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                    .all()
                )
                settings_serialized = serialize_settings(settings)

                # Serializar o componente para os templates
                application_component_serialized = serialize_application_component(db_cron)
                component_type = db_cron.type.value if hasattr(db_cron.type, 'value') else str(db_cron.type)

                # Gerar payload do Kubernetes
                k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
                kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                    application_component_serialized, component_type, settings_serialized, db=db
                )

                # Deletar recursos no Kubernetes
                k8s_client.apply_or_delete_yaml_to_k8s(
                    kubernetes_payload, operation="delete"
                )
            except Exception as e:
                # Se falhar ao deletar no Kubernetes, ainda deletamos o componente e cluster_instance do banco
                # mas logamos o erro
                print(f"Error deleting resources from Kubernetes: {e}")

        # Deletar o cluster_instance e o componente do banco
        try:
            if cluster_instance:
                db.delete(cluster_instance)
            db.delete(db_cron)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e._sql_message}"}
            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Cron deleted successfully"}

