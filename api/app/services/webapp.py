from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4
from uuid import UUID

import app.models.application_components as ApplicationComponentModel
import app.models.instance as InstanceModel
import app.models.cluster_instance as ClusterInstanceModel
import app.models.settings as SettingsModel
import app.schemas.webapp as WebappSchema
from app.helpers.serializers import serialize_application_component, serialize_settings
from app.k8s.client import K8sClient
from app.services.kubernetes.application_component_manager import (
    KubernetesApplicationComponentManager,
)
from app.services.cluster_selection import ClusterSelectionService
from app.services.cluster import get_gateway_reference_from_cluster


def validate_exposure_type_in_gateway_resources(cluster, exposure_type: str):
    """
    Valida se o exposure.type está disponível nos recursos do Gateway API do cluster.

    Args:
        cluster: Objeto Cluster do banco de dados
        exposure_type: Tipo de exposição ('http', 'tcp', 'udp')

    Raises:
        HTTPException: Se o recurso necessário não estiver disponível no cluster
    """
    # Mapeamento de exposure.type para recursos do Gateway API
    type_to_resource = {
        'http': 'HTTPRoute',
        'tcp': 'TCPRoute',
        'udp': 'UDPRoute'
    }

    required_resource = type_to_resource.get(exposure_type)
    if not required_resource:
        # Se não for um tipo que requer Gateway API, não precisa validar
        return

    # Verificar Gateway API e recursos disponíveis
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")

    if not gateway_api_available:
        raise HTTPException(
            status_code=400,
            detail=f"Gateway API is not available in cluster '{cluster.name}'. Exposure type '{exposure_type}' requires Gateway API support."
        )

    gateway_resources = k8s_client.get_gateway_api_resources()

    if required_resource not in gateway_resources:
        raise HTTPException(
            status_code=400,
            detail=f"Gateway API resource '{required_resource}' is not available in cluster '{cluster.name}'. Required for exposure type '{exposure_type}'. Available resources: {', '.join(gateway_resources) if gateway_resources else 'none'}"
        )


class WebappService:
    @staticmethod
    def upsert_webapp(
        db: Session,
        webapp: WebappSchema.WebappCreate | WebappSchema.WebappUpdate,
        uuid: UUID = None,
    ):
        if uuid:
            # Update existing webapp
            db_webapp = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
                .first()
            )

            if db_webapp is None:
                raise HTTPException(status_code=404, detail="Webapp not found")

            if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
                raise HTTPException(
                    status_code=400,
                    detail="Component is not a webapp"
                )

            # Cast to WebappUpdate for type checking
            webapp_update = WebappSchema.WebappUpdate.model_validate(webapp)

            # Verificar se houve mudança no enabled
            enabled_changed = webapp_update.enabled is not None and webapp_update.enabled != db_webapp.enabled
            was_enabled = db_webapp.enabled
            will_be_enabled = webapp_update.enabled if webapp_update.enabled is not None else db_webapp.enabled

            if webapp_update.settings is not None:
                settings_dict = webapp_update.settings.model_dump()

                # Validar exposure.type se presente nos settings
                if 'exposure' in settings_dict and 'type' in settings_dict['exposure']:
                    exposure_type = settings_dict['exposure']['type']

                    # Buscar o cluster_instance relacionado ao componente
                    temp_cluster_instance = (
                        db.query(ClusterInstanceModel.ClusterInstance)
                        .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
                        .first()
                    )

                    # Se não existir cluster_instance, precisamos obter um cluster para validar
                    if temp_cluster_instance is None:
                        instance = db_webapp.instance
                        temp_cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                            db, instance.environment_id, instance.environment.name
                        )
                    else:
                        temp_cluster = temp_cluster_instance.cluster

                    # Validar se o exposure.type está disponível nos recursos do Gateway API
                    validate_exposure_type_in_gateway_resources(temp_cluster, exposure_type)

                # Validar exposure.visibility se presente nos settings
                if 'exposure' in settings_dict and 'visibility' in settings_dict['exposure']:
                    exposure_visibility = settings_dict['exposure']['visibility']
                    if exposure_visibility in ['public', 'private']:
                        # Buscar o cluster_instance relacionado ao componente
                        temp_cluster_instance = (
                            db.query(ClusterInstanceModel.ClusterInstance)
                            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
                            .first()
                        )

                        # Se não existir cluster_instance, precisamos obter um cluster para validar
                        if temp_cluster_instance is None:
                            instance = db_webapp.instance
                            temp_cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                                db, instance.environment_id, instance.environment.name
                            )
                        else:
                            temp_cluster = temp_cluster_instance.cluster

                        # Verificar se o cluster tem gateway_api disponível
                        k8s_client_temp = K8sClient(url=temp_cluster.api_address, token=temp_cluster.token)
                        gateway_api_available = k8s_client_temp.check_api_available("gateway.networking.k8s.io")

                        if not gateway_api_available:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Cluster '{temp_cluster.name}' does not have Gateway API available. Visibility 'public' or 'private' requires Gateway API support. Please use 'cluster' visibility instead."
                            )
                db_webapp.settings = settings_dict

            # Obter exposure_type e visibility após atualizar settings
            final_settings = db_webapp.settings or {}
            exposure_type = final_settings.get('exposure', {}).get('type', 'http')
            exposure_visibility = final_settings.get('exposure', {}).get('visibility', 'cluster')

            # Em um PUT, verificar se o campo url foi enviado no payload
            # Usar model_fields_set do Pydantic v2 para verificar campos definidos
            url_present_in_payload = 'url' in webapp_update.model_fields_set if hasattr(webapp_update, 'model_fields_set') else webapp_update.url is not None

            # Se exposure.type não for HTTP ou visibility for cluster, limpar URL automaticamente
            if exposure_type != 'http' or exposure_visibility == 'cluster':
                db_webapp.url = None
            elif url_present_in_payload:
                # Se o campo url veio no payload, atualizar/limpar conforme o valor
                if webapp_update.url is not None:
                    # Se for HTTP e visibility não for cluster e URL foi enviada, atualizar
                    db_webapp.url = webapp_update.url
                else:
                    # Se url veio como None no payload (ou não veio), remover do banco
                    db_webapp.url = None
            # Se url não veio no payload, manter o valor atual do banco (não fazer nada)

            if webapp_update.enabled is not None:
                db_webapp.enabled = webapp_update.enabled

            # Validate that webapp requires url only if exposure.type is 'http' and visibility is not 'cluster'
            final_url = db_webapp.url
            if exposure_type == 'http' and exposure_visibility != 'cluster' and not final_url:
                raise HTTPException(
                    status_code=400,
                    detail="URL is required for webapp components with HTTP exposure type and visibility 'public' or 'private'"
                )

            # Buscar o cluster_instance relacionado ao componente
            cluster_instance = (
                db.query(ClusterInstanceModel.ClusterInstance)
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
                .first()
            )

            # Se não existir, criar automaticamente usando o cluster de menor carga
            if cluster_instance is None:
                instance = db_webapp.instance
                cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                    db, instance.environment_id, instance.environment.name
                )

                # Criar novo cluster_instance
                cluster_instance = ClusterInstanceModel.ClusterInstance(
                    uuid=uuid4(),
                    cluster_id=cluster.id,
                    application_component_id=db_webapp.id,
                )
                db.add(cluster_instance)
            else:
                cluster = cluster_instance.cluster

            # Buscar settings do environment
            instance = db_webapp.instance
            settings = (
                db.query(SettingsModel.Settings)
                .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                .all()
            )
            settings_serialized = serialize_settings(settings)

            # Recarregar o componente com relacionamentos para serialização usando joinedload
            db_webapp = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_webapp.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_webapp)
            component_type = db_webapp.type.value if hasattr(db_webapp.type, 'value') else str(db_webapp.type)

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
                    db.refresh(db_webapp)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    # Log do erro mas continua com a atualização do banco
                    print(f"Error removing component '{db_webapp.name}' from Kubernetes: {e}")
                    db.commit()
                    db.refresh(db_webapp)
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
                    db.refresh(db_webapp)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to reapply component to Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

            # Se não houve mudança no enabled ou se está habilitado, aplicar normalmente
            elif not enabled_changed or db_webapp.enabled:
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
                    db.refresh(db_webapp)
                    if cluster_instance:
                        db.refresh(cluster_instance)
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to update component in Kubernetes cluster '{cluster.name}': {str(e)}"
                    )

        else:
            # Create new webapp
            # Cast to WebappCreate for type checking
            webapp_create = WebappSchema.WebappCreate.model_validate(webapp)

            # Validate URL based on exposure.type and visibility
            settings_dict = webapp_create.settings.model_dump() if webapp_create.settings else {}
            exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
            exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

            # URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
            if exposure_type == 'http' and exposure_visibility != 'cluster' and not webapp_create.url:
                raise HTTPException(
                    status_code=400,
                    detail="URL is required for webapp components with HTTP exposure type and visibility 'public' or 'private'"
                )
            # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
            if (exposure_type != 'http' or exposure_visibility == 'cluster') and webapp_create.url:
                if exposure_type != 'http':
                    raise HTTPException(
                        status_code=400,
                        detail=f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type."
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility."
                    )

            # Get instance by uuid
            instance = (
                db.query(InstanceModel.Instance)
                .filter(InstanceModel.Instance.uuid == webapp_create.instance_uuid)
                .first()
            )
            if instance is None:
                raise HTTPException(status_code=404, detail="Instance not found")

            # Validar exposure.type e exposure.visibility se presente nos settings
            settings_dict = webapp_create.settings.model_dump()
            cluster = None

            # Validar exposure.type se presente
            if 'exposure' in settings_dict and 'type' in settings_dict['exposure']:
                exposure_type = settings_dict['exposure']['type']

                # Obter o cluster que será usado (cluster de menor carga)
                cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                    db, instance.environment_id, instance.environment.name
                )

                # Validar se o exposure.type está disponível nos recursos do Gateway API
                validate_exposure_type_in_gateway_resources(cluster, exposure_type)

            # Validar exposure.visibility se presente nos settings
            if 'exposure' in settings_dict and 'visibility' in settings_dict['exposure']:
                exposure_visibility = settings_dict['exposure']['visibility']
                if exposure_visibility in ['public', 'private']:
                    # Obter o cluster que será usado (cluster de menor carga) se ainda não foi obtido
                    if cluster is None:
                        cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                            db, instance.environment_id, instance.environment.name
                        )

                    # Verificar se o cluster tem gateway_api disponível
                    k8s_client_temp = K8sClient(url=cluster.api_address, token=cluster.token)
                    gateway_api_available = k8s_client_temp.check_api_available("gateway.networking.k8s.io")

                    if not gateway_api_available:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cluster '{cluster.name}' does not have Gateway API available. Visibility 'public' or 'private' requires Gateway API support. Please use 'cluster' visibility instead."
                        )

            db_webapp = ApplicationComponentModel.ApplicationComponent(
                uuid=uuid4(),
                instance_id=instance.id,
                name=webapp_create.name,
                type=ApplicationComponentModel.WebappType.webapp,
                settings=settings_dict,
                url=webapp_create.url,
                enabled=webapp_create.enabled,
            )
            db.add(db_webapp)

            try:
                db.commit()
                db.refresh(db_webapp)
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"{e._sql_message}"}
                raise HTTPException(status_code=400, detail=message)

            # Criar cluster_instance automaticamente usando o cluster de menor carga
            # Se já obtivemos o cluster acima (para validação), reutilizar; caso contrário, obter agora
            if cluster is None:
                cluster = ClusterSelectionService.get_cluster_with_least_load_or_raise(
                    db, instance.environment_id, instance.environment.name
                )

            # Verificar se já existe um cluster_instance para este componente (não deveria acontecer em criação)
            existing_cluster_instance = (
                db.query(ClusterInstanceModel.ClusterInstance)
                .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
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
                    application_component_id=db_webapp.id,
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
            db_webapp = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .options(
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.application),
                    joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                    .joinedload(InstanceModel.Instance.environment)
                )
                .filter(ApplicationComponentModel.ApplicationComponent.id == db_webapp.id)
                .first()
            )

            # Serializar o componente para os templates
            application_component_serialized = serialize_application_component(db_webapp)
            component_type = db_webapp.type.value if hasattr(db_webapp.type, 'value') else str(db_webapp.type)

            # Aplicar recursos no Kubernetes
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
                    kubernetes_payload, operation="create"
                )

                # Commit do cluster_instance e do componente
                db.commit()
                db.refresh(cluster_instance)
                db.refresh(db_webapp)
            except Exception as e:
                db.rollback()
                # Se falhar ao aplicar no Kubernetes, removemos o componente criado
                # para manter a consistência
                db.delete(db_webapp)
                if not existing_cluster_instance:
                    # Se criamos um cluster_instance, removemos também
                    if cluster_instance in db:
                        db.delete(cluster_instance)
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to deploy component to Kubernetes cluster '{cluster.name}': {str(e)}"
                )

        return db_webapp

    def get_webapp(
        db: Session, uuid: UUID
    ) -> WebappSchema.Webapp:
        db_webapp = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )
        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )
        return WebappSchema.Webapp.model_validate(db_webapp)

    def get_webapps(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[WebappSchema.Webapp]:
        db_webapps = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.webapp)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [WebappSchema.Webapp.model_validate(webapp) for webapp in db_webapps]

    @staticmethod
    def delete_webapp(db: Session, uuid: UUID):
        # Buscar o componente com relacionamentos
        db_webapp = (
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

        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )

        # Buscar o cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
            .first()
        )

        # Se existir cluster_instance, deletar os recursos no Kubernetes
        if cluster_instance:
            try:
                cluster = cluster_instance.cluster

                # Buscar settings do environment
                instance = db_webapp.instance
                settings = (
                    db.query(SettingsModel.Settings)
                    .filter(SettingsModel.Settings.environment_id == instance.environment_id)
                    .all()
                )
                settings_serialized = serialize_settings(settings)

                # Serializar o componente para os templates
                application_component_serialized = serialize_application_component(db_webapp)
                component_type = db_webapp.type.value if hasattr(db_webapp.type, 'value') else str(db_webapp.type)

                # Gerar payload do Kubernetes
                k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
                gateway_reference = get_gateway_reference_from_cluster(cluster)
                kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                    application_component_serialized, component_type, settings_serialized, db=db,
                    gateway_reference=gateway_reference
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
            db.delete(db_webapp)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e._sql_message}"}
            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Webapp deleted successfully"}

    @staticmethod
    def get_webapp_pods(db: Session, uuid: UUID):
        """
        Busca os pods do Kubernetes relacionados a um webapp.
        """
        # Buscar o componente com relacionamentos
        db_webapp = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .options(
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.application),
                joinedload(ApplicationComponentModel.ApplicationComponent.instance)
                .joinedload(InstanceModel.Instance.environment),
                joinedload(ApplicationComponentModel.ApplicationComponent.instances)
                .joinedload(ClusterInstanceModel.ClusterInstance.cluster)
            )
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )

        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Webapp is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_webapp.instance.application.name
        component_name = db_webapp.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Listar pods usando label selector baseado no nome do componente
        # O label selector pode variar dependendo de como os pods são rotulados
        # Vamos tentar alguns padrões comuns
        label_selector = f"app={component_name}"
        pods = k8s_client.list_pods(namespace=application_name, label_selector=label_selector)

        # Se não encontrar com esse seletor, tentar sem seletor e filtrar depois
        if not pods:
            all_pods = k8s_client.list_pods(namespace=application_name)
            pods = [pod for pod in all_pods if component_name in pod['name']]

        return pods

    @staticmethod
    def delete_webapp_pod(db: Session, uuid: UUID, pod_name: str):
        """
        Deleta um pod específico do Kubernetes relacionado a um webapp.
        """
        # Buscar o componente com relacionamentos
        db_webapp = (
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

        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Webapp is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_webapp.instance.application.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Deletar o pod
        try:
            k8s_client.delete_pod(namespace=application_name, pod_name=pod_name)
            return {"detail": f"Pod {pod_name} deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete pod {pod_name}: {str(e)}"
            )

    @staticmethod
    def get_webapp_pod_logs(db: Session, uuid: UUID, pod_name: str, container_name: str = None, tail_lines: int = 100):
        """
        Obtém os logs de um pod específico do Kubernetes relacionado a um webapp.
        """
        # Buscar o componente com relacionamentos
        db_webapp = (
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

        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Webapp is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_webapp.instance.application.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Obter logs do pod
        try:
            logs = k8s_client.get_pod_logs(
                namespace=application_name,
                pod_name=pod_name,
                container_name=container_name,
                tail_lines=tail_lines
            )
            return {"logs": logs, "pod_name": pod_name, "container_name": container_name}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get logs for pod {pod_name}: {str(e)}"
            )

    @staticmethod
    def exec_webapp_pod_command(db: Session, uuid: UUID, pod_name: str, command: list[str], container_name: str = None):
        """
        Executa um comando em um pod específico do Kubernetes relacionado a um webapp.
        """
        # Buscar o componente com relacionamentos
        db_webapp = (
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

        if db_webapp is None:
            raise HTTPException(status_code=404, detail="Webapp not found")
        if db_webapp.type != ApplicationComponentModel.WebappType.webapp:
            raise HTTPException(
                status_code=400,
                detail="Component is not a webapp"
            )

        # Buscar cluster_instance relacionado
        cluster_instance = (
            db.query(ClusterInstanceModel.ClusterInstance)
            .filter(ClusterInstanceModel.ClusterInstance.application_component_id == db_webapp.id)
            .first()
        )

        if not cluster_instance:
            raise HTTPException(
                status_code=404,
                detail="Webapp is not deployed to any cluster"
            )

        cluster = cluster_instance.cluster
        application_name = db_webapp.instance.application.name

        # Criar cliente Kubernetes
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        # Executar comando no pod
        try:
            result = k8s_client.exec_pod_command(
                namespace=application_name,
                pod_name=pod_name,
                command=command,
                container_name=container_name
            )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to execute command in pod {pod_name}: {str(e)}"
            )

