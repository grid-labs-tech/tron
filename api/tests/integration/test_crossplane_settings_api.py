"""Integration tests for environment Crossplane config API."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from uuid import uuid4

from app.environments.infra.environment_model import Environment
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.infra.environment_settings_model import EnvironmentSettings
from app.environments.infra.environment_settings_repository import (
    EnvironmentSettingsRepository,
)
from app.environments.core.environment_settings_defaults import (
    DEFAULT_ENVIRONMENT_SETTINGS,
)
from app.clusters.infra.cluster_model import Cluster
from app.clusters.infra.cluster_repository import ClusterRepository


@pytest.fixture
def test_environment_with_settings(test_db, admin_user, test_organization):
    """Environment with default settings row."""
    env_repo = EnvironmentRepository(test_db)
    environment = env_repo.create(
        Environment(name="crossplane-env", organization_id=test_organization.id)
    )
    settings_repo = EnvironmentSettingsRepository(test_db)
    settings_repo.create(
        EnvironmentSettings(
            uuid=uuid4(),
            environment_id=environment.id,
            organization_id=test_organization.id,
            settings=[dict(item) for item in DEFAULT_ENVIRONMENT_SETTINGS],
        )
    )
    test_db.commit()
    test_db.refresh(environment)
    environment.organization = test_organization
    return environment


@pytest.fixture
def crossplane_cluster(test_db, test_environment_with_settings):
    """Cluster in the environment (health verified live on Crossplane enable)."""
    cluster_repo = ClusterRepository(test_db)
    cluster = cluster_repo.create(
        Cluster(
            uuid=uuid4(),
            name="crossplane-cluster",
            api_address="https://k8s-crossplane.example.com",
            token="token",
            environment_id=test_environment_with_settings.id,
        )
    )
    test_db.commit()
    test_db.refresh(cluster)
    return cluster


def _crossplane_url(organization, environment):
    return (
        f"/organizations/{organization.uuid}/environments/{environment.uuid}/crossplane"
    )


def test_get_crossplane_config_defaults(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
):
    response = client.get(
        _crossplane_url(test_organization, test_environment_with_settings),
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["enabled"] is False
    assert data["cluster_uuid"] is None
    assert data["aws_region"] == ""
    assert data["aws_account_id"] == ""
    assert data["provider_config"] == ""


@patch("app.crossplane.api.crossplane_handlers.probe_crossplane_health")
def test_update_crossplane_config_success(
    mock_probe,
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    mock_probe.return_value = {
        "available": True,
        "healthy": True,
        "providers": [{"name": "provider-aws-sqs", "healthy": True}],
    }
    response = client.put(
        _crossplane_url(test_organization, test_environment_with_settings),
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "enabled": True,
            "cluster_uuid": str(crossplane_cluster.uuid),
            "aws_region": "us-east-1",
            "aws_account_id": "000000000000",
            "provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["enabled"] is True
    assert data["cluster_uuid"] == str(crossplane_cluster.uuid)
    assert data["aws_region"] == "us-east-1"
    assert data["aws_account_id"] == "000000000000"
    assert data["provider_config"] == "floci"
    mock_probe.assert_called_once()


@patch("app.crossplane.api.crossplane_handlers.probe_crossplane_health")
def test_update_crossplane_config_rejects_unhealthy_cluster(
    mock_probe,
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    mock_probe.return_value = {
        "available": True,
        "healthy": False,
        "providers": [{"name": "provider-aws-sqs", "healthy": False}],
    }
    response = client.put(
        _crossplane_url(test_organization, test_environment_with_settings),
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "enabled": True,
            "cluster_uuid": str(crossplane_cluster.uuid),
            "aws_region": "us-east-1",
            "aws_account_id": "000000000000",
            "provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not healthy" in response.json()["detail"].lower()


def test_update_crossplane_config_invalid_region(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    response = client.put(
        _crossplane_url(test_organization, test_environment_with_settings),
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "enabled": True,
            "cluster_uuid": str(crossplane_cluster.uuid),
            "aws_region": "not-a-region",
            "aws_account_id": "000000000000",
            "provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "aws_region" in response.json()["detail"]


def test_environment_settings_do_not_include_crossplane_keys(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    org_uuid = str(test_organization.uuid)
    env_uuid = str(test_environment_with_settings.uuid)

    response = client.get(
        f"/organizations/{org_uuid}/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["clusters"]) == 1
    cluster = data["clusters"][0]
    assert cluster["uuid"] == str(crossplane_cluster.uuid)
    assert cluster["name"] == crossplane_cluster.name
    assert "crossplane_available" not in cluster
    setting_keys = {item["key"] for item in data["settings"]}
    assert "crossplane_enabled" not in setting_keys
    assert "crossplane_cluster_uuid" not in setting_keys
    assert "crossplane_aws_region" not in setting_keys
    assert "crossplane_provider_config" not in setting_keys
    assert "crossplane_aws_account_id" not in setting_keys


@patch("app.clusters.core.cluster_service.K8sClient")
def test_create_cluster_ignores_legacy_crossplane_available_field(
    mock_k8s_client,
    client,
    admin_token,
    test_environment_with_settings,
):
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (
        True,
        {"message": "Connection successful"},
    )
    mock_k8s_client.return_value = mock_client_instance

    org_uuid = str(test_environment_with_settings.organization.uuid)
    response = client.post(
        f"/organizations/{org_uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "cp-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token",
            "environment_uuid": str(test_environment_with_settings.uuid),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "crossplane_available" not in response.json()
