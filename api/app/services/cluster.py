import json

from fastapi import HTTPException
from app.k8s.client import K8sClient
from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID

import app.models.cluster as ClusterModel
import app.models.environment as EnvironmentModel
import app.schemas.cluster as ClusterSchema


def get_gateway_reference_from_cluster(cluster) -> dict:
    """
    Obtém as informações de referência do gateway de um cluster.
    Busca dinamicamente o Gateway no cluster Kubernetes.

    Args:
        cluster: Objeto Cluster do banco de dados

    Returns:
        Dict com namespace e name do gateway, ou valores vazios se não encontrar
    """
    try:
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
        gateway_ref = k8s_client.get_gateway_reference()

        if gateway_ref:
            return gateway_ref
    except Exception as e:
        print(f"Warning: Error getting Gateway reference from cluster: {e}")

    # Retornar valores vazios se não encontrar
    return {
        "namespace": "",
        "name": ""
    }


class ClusterService:
    def upsert_cluster(
        db: Session, cluster: ClusterSchema.ClusterCreate, cluster_uuid: UUID = None
    ):

        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

        try:
            success, connection_message = k8s_client.validate_connection()
            if not success:
                # connection_message é um dict com status e message
                error_message = connection_message.get("message", {})
                if isinstance(error_message, dict):
                    error_text = error_message.get("message", json.dumps(error_message))
                else:
                    error_text = str(error_message)
                raise HTTPException(status_code=400, detail=error_text)
        except HTTPException:
            raise
        except Exception as e:
            error_message = str(e)
            raise HTTPException(status_code=400, detail=f"Connection validation failed: {error_message}")

        if cluster_uuid:
            db_cluster = (
                db.query(ClusterModel.Cluster)
                .filter(ClusterModel.Cluster.uuid == cluster_uuid)
                .first()
            )
            if db_cluster:
                db_cluster.name = cluster.name
                db_cluster.api_address = cluster.api_address
                db_cluster.token = cluster.token
                try:
                    db.commit()
                except Exception as e:
                    error_msg = str(e) if hasattr(e, '__str__') else f"{e}"
                    raise HTTPException(status_code=400, detail=error_msg)
                db.refresh(db_cluster)
                return db_cluster

        environment = (
            db.query(EnvironmentModel.Environment)
            .filter(EnvironmentModel.Environment.uuid == cluster.environment_uuid)
            .first()
        )

        if not environment:
            raise HTTPException(status_code=404, detail="Environment not found")

        new_cluster = ClusterModel.Cluster(
            uuid=uuid4(),
            name=cluster.name,
            api_address=cluster.api_address,
            token=cluster.token,
            environment_id=environment.id,
        )

        db.add(new_cluster)

        try:
            db.commit()
        except Exception as e:
            error_msg = str(e) if hasattr(e, '__str__') else f"{e}"
            raise HTTPException(status_code=400, detail=error_msg)

        db.refresh(new_cluster)

        return new_cluster

    def get_cluster(db: Session, uuid: int):

        db_cluster = (
            db.query(ClusterModel.Cluster)
            .filter(ClusterModel.Cluster.uuid == uuid)
            .first()
        )

        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")

        k8s_client = K8sClient(url=db_cluster.api_address, token=db_cluster.token)

        available_cpu = k8s_client.get_available_cpu() or 0
        available_memory = k8s_client.get_available_memory() or 0

        # Verificar Gateway API e recursos disponíveis
        gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")
        gateway_resources = []
        gateway_reference = {
            "namespace": "",
            "name": "",
        }

        if gateway_api_available:
            gateway_resources = k8s_client.get_gateway_api_resources()
            # Buscar referência do Gateway no cluster
            gateway_ref = k8s_client.get_gateway_reference()
            if gateway_ref:
                gateway_reference = gateway_ref

        serialized_data = {
            "uuid": db_cluster.uuid,
            "name": db_cluster.name,
            "api_address": db_cluster.api_address,
            "available_cpu": available_cpu,
            "available_memory": available_memory,
            "environment": db_cluster.environment,
            "gateway": {
                "api": {
                    "enabled": gateway_api_available,
                    "resources": gateway_resources,
                },
                "reference": gateway_reference,
            },
        }

        return ClusterSchema.ClusterCompletedResponse.model_validate(serialized_data)

    def get_clusters(db: Session, skip: int = 0, limit: int = 100):
        clusters = db.query(ClusterModel.Cluster).offset(skip).limit(limit).all()

        serialized_data = []

        for cluster in clusters:
            k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
            success, connection_message = k8s_client.validate_connection()

            # Verificar se a API Gateway está disponível apenas se a conexão for bem-sucedida
            gateway_api_available = False
            gateway_resources = []
            gateway_reference = {
                "namespace": "",
                "name": "",
            }

            if success:
                gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")
                if gateway_api_available:
                    gateway_resources = k8s_client.get_gateway_api_resources()
                    # Buscar referência do Gateway no cluster
                    gateway_ref = k8s_client.get_gateway_reference()
                    if gateway_ref:
                        gateway_reference = gateway_ref

            cluster_data = {
                "uuid": cluster.uuid,
                "name": cluster.name,
                "api_address": cluster.api_address,
                "environment": cluster.environment,
                "detail": connection_message,
                "gateway": {
                    "api": {
                        "enabled": gateway_api_available,
                        "resources": gateway_resources,
                    },
                    "reference": gateway_reference,
                },
            }

            cluster_response = (
                ClusterSchema.ClusterResponseWithValidation.model_validate(cluster_data)
            )
            serialized_data.append(cluster_response)

        return serialized_data

    def delete_cluster(db: Session, cluster_uuid: UUID):
        db_cluster = (
            db.query(ClusterModel.Cluster)
            .filter(ClusterModel.Cluster.uuid == cluster_uuid)
            .first()
        )

        if not db_cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        db.delete(db_cluster)
        db.commit()

        return {"detail": "Cluster deleted successfully"}
