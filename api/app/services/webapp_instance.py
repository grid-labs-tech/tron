from fastapi import HTTPException

import app.models.cluster_instance as InstanceModel
import app.models.application_components as ApplicationComponentModel
import app.models.cluster as ClusterModel
import app.models.environment as EnvironmentModel
import app.models.settings as SettingsModel
import app.schemas.instance as InstanceSchema

from app.helpers.serializers import serialize_application_component, serialize_settings
from app.k8s.client import K8sClient
from app.services.kubernetes.application_component_manager import (
    KubernetesApplicationComponentManager,
)
from app.services.cluster import get_gateway_reference_from_cluster

from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class InstanceService:
    def get_instance(db: Session, instance_uuid: int):
        db_instance = (
            db.query(InstanceModel.ClusterInstance)
            .filter(InstanceModel.ClusterInstance.uuid == instance_uuid)
            .first()
        )

        if db_instance is None:
            raise HTTPException(status_code=404, detail="Instance not found")

        return InstanceSchema.Instance.model_validate(db_instance)

    def get_instances(db: Session, skip: int = 0, limit: int = 100):
        db_instances = db.query(InstanceModel.ClusterInstance).offset(skip).limit(limit).all()

        return db_instances

    def delete_instance(db: Session, instance_uuid: UUID):

        db_instance = (
            db.query(InstanceModel.ClusterInstance)
            .filter(InstanceModel.ClusterInstance.uuid == instance_uuid)
            .first()
        )
        if db_instance is None:
            raise HTTPException(status_code=404, detail="Instance not found")

        application_component = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(
                ApplicationComponentModel.ApplicationComponent.uuid == db_instance.application_component.uuid
            )
            .first()
        )

        cluster = (
            db.query(ClusterModel.Cluster)
            .filter(ClusterModel.Cluster.uuid == db_instance.cluster.uuid)
            .first()
        )

        try:

            application_component_serialized = serialize_application_component(application_component)
            component_type = application_component.type.value if hasattr(application_component.type, 'value') else str(application_component.type)

            gateway_reference = get_gateway_reference_from_cluster(cluster)
            kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                application_component_serialized, component_type, db=db,
                gateway_reference=gateway_reference
            )

            k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
            k8s_client.apply_or_delete_yaml_to_k8s(
                kubernetes_payload, operation="delete"
            )

            db.delete(db_instance)
            db.commit()
        except Exception as e:
            message = {"status": "error", "message": f"{e}"}

            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Instance deleted successfully"}

    def upsert_instance(
        db: Session,
        instance: InstanceSchema.InstanceCreate,
        instance_uuid: UUID = None,
    ):

        cluster = (
            db.query(ClusterModel.Cluster)
            .filter(ClusterModel.Cluster.uuid == instance.cluster_uuid)
            .first()
        )

        application_component = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == instance.application_component_uuid)
            .first()
        )

        settings = (
            db.query(SettingsModel.Settings)
            .filter(SettingsModel.Settings.environment_id == application_component.instance.environment_id)
            .all()
        )

        if cluster.environment.uuid != application_component.instance.environment.uuid:
            raise HTTPException(
                status_code=400, detail="Cluster is not associated with the environment"
            )

        if instance_uuid:
            db_instance = (
                db.query(InstanceModel.ClusterInstance)
                .filter(InstanceModel.ClusterInstance.uuid == instance_uuid)
                .first()
            )
            if db_instance:
                db_instance.cluster_id = cluster.id
                db_instance.application_component_id = application_component.id
                try:

                    application_component_serialized = serialize_application_component(application_component)
                    component_type = application_component.type.value if hasattr(application_component.type, 'value') else str(application_component.type)
                    settings_serialized = serialize_settings(settings)

                    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
                    gateway_reference = get_gateway_reference_from_cluster(cluster)
                    kubernetes_payload = (
                        KubernetesApplicationComponentManager.instance_management(
                            application_component_serialized, component_type, settings_serialized, db=db,
                            gateway_reference=gateway_reference
                        )
                    )
                    k8s_client.apply_or_delete_yaml_to_k8s(
                        kubernetes_payload, operation="create"
                    )

                    db.commit()
                    db.refresh(db_instance)
                except Exception as e:
                    db.rollback()
                    message = {"status": "error", "message": f"{e}"}
                    raise HTTPException(status_code=400, detail=message)
                return db_instance

        new_instance = InstanceModel.ClusterInstance(
            uuid=uuid4(), cluster_id=cluster.id, application_component_id=application_component.id
        )
        db.add(new_instance)

        try:

            application_component_serialized = serialize_application_component(application_component)
            component_type = application_component.type.value if hasattr(application_component.type, 'value') else str(application_component.type)
            settings_serialized = serialize_settings(settings)

            k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
            gateway_reference = get_gateway_reference_from_cluster(cluster)
            kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
                application_component_serialized, component_type, settings_serialized, db=db,
                gateway_reference=gateway_reference
            )
            k8s_client.apply_or_delete_yaml_to_k8s(
                kubernetes_payload, operation="create"
            )

            db.commit()
            db.refresh(new_instance)

        except Exception as e:

            db.rollback()
            message = {"status": "error", "message": f"{e}"}

            raise HTTPException(status_code=400, detail=message)
        return new_instance
