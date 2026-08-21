"""Integration tests for clusters endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from uuid import uuid4


@pytest.fixture
def test_environment(test_db, admin_user, test_organization):
    """Create a test environment."""
    from app.environments.infra.environment_model import Environment
    from app.environments.infra.environment_repository import EnvironmentRepository

    environment_repo = EnvironmentRepository(test_db)
    environment = Environment(
        name="test-environment",
        organization_id=test_organization.id
    )
    environment = environment_repo.create(environment)
    test_db.commit()
    test_db.refresh(environment)
    # Add organization relationship for easy access
    environment.organization = test_organization
    return environment


@patch('app.clusters.core.cluster_service.K8sClient')
def test_create_cluster_success(mock_k8s_client, client, admin_token, test_environment):
    """Test successful cluster creation."""
    # Mock Kubernetes connection validation
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_k8s_client.return_value = mock_client_instance

    response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-cluster"
    assert data["api_address"] == "https://k8s.example.com"
    assert "uuid" in data
    # Note: ClusterResponse includes token in ClusterBase, so token is in response
    assert "token" in data


def test_create_cluster_requires_authentication(client, test_environment):
    """Test that cluster creation requires authentication."""
    response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_cluster_requires_admin_role(client, user_token, test_environment):
    """Test that cluster creation requires admin role."""
    response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_cluster_invalid_environment(client, admin_token, test_organization):
    """Test cluster creation with invalid environment UUID."""
    response = client.post(
        f"/organizations/{test_organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(uuid4())
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_cluster_missing_fields(client, admin_token, test_environment):
    """Test cluster creation with missing required fields."""
    response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster"
            # Missing api_address, token, environment_uuid
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch('app.crossplane.infra.k8s_crossplane_probe.K8sClient')
@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.clusters.core.cluster_service.K8sClient')
def test_list_clusters_success(
    mock_k8s_client, mock_gateway_ref, mock_probe_k8s_client, client, admin_token, test_environment
):
    """Test successful cluster listing."""
    # Mock Kubernetes connection validation
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_client_instance.check_api_available.return_value = False
    mock_k8s_client.return_value = mock_client_instance
    mock_gateway_ref.return_value = {"namespace": "", "name": ""}

    mock_probe_client = MagicMock()
    mock_probe_client.validate_connection.return_value = (True, {"message": "ok"})
    mock_probe_client.check_crossplane_status.return_value = {
        "available": False,
        "healthy": False,
        "providers": [],
    }
    mock_probe_k8s_client.return_value = mock_probe_client

    # First create a cluster
    create_response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )
    assert create_response.status_code == status.HTTP_200_OK

    # Then list clusters
    response = client.get(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    listed = next(c for c in data if c["name"] == "test-cluster")
    assert listed["crossplane"] == {
        "available": False,
        "healthy": False,
        "providers": [],
    }
    assert "crossplane_available" not in listed


def test_list_clusters_requires_authentication(client, test_organization):
    """Test that listing clusters requires authentication."""
    response = client.get(f"/organizations/{test_organization.uuid}/clusters/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch('app.crossplane.infra.k8s_crossplane_probe.K8sClient')
@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.clusters.core.cluster_service.K8sClient')
def test_get_cluster_success(
    mock_k8s_client, mock_gateway_ref, mock_probe_k8s_client, client, admin_token, test_environment
):
    """Test successful cluster retrieval."""
    # Mock Kubernetes connection validation and gateway methods
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_client_instance.check_api_available.return_value = False
    mock_client_instance.get_gateway_api_resources.return_value = []
    mock_client_instance.get_available_cpu.return_value = None
    mock_client_instance.get_available_memory.return_value = None
    mock_k8s_client.return_value = mock_client_instance
    mock_gateway_ref.return_value = {"namespace": "", "name": ""}

    mock_probe_client = MagicMock()
    mock_probe_client.validate_connection.return_value = (True, {"message": "ok"})
    mock_probe_client.check_crossplane_status.return_value = {
        "available": True,
        "healthy": True,
        "providers": [{"name": "provider-aws", "healthy": True}],
    }
    mock_probe_k8s_client.return_value = mock_probe_client

    # First create a cluster
    create_response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )
    cluster_uuid = create_response.json()["uuid"]

    # Mock again for get_cluster (which calls K8sClient again)
    mock_k8s_client.return_value = mock_client_instance

    # Then get the cluster
    response = client.get(
        f"/organizations/{test_environment.organization.uuid}/clusters/{cluster_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-cluster"
    assert data["uuid"] == cluster_uuid
    assert data["crossplane"] == {
        "available": True,
        "healthy": True,
        "providers": [{"name": "provider-aws", "healthy": True}],
    }
    assert "crossplane_available" not in data


def test_get_cluster_not_found(client, admin_token, test_organization):
    """Test getting non-existent cluster."""
    response = client.get(
        f"/organizations/{test_organization.uuid}/clusters/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch('app.clusters.core.cluster_service.K8sClient')
def test_update_cluster_success(mock_k8s_client, client, admin_token, test_environment):
    """Test successful cluster update."""
    # Mock Kubernetes connection validation
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_k8s_client.return_value = mock_client_instance

    # First create a cluster
    create_response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )
    cluster_uuid = create_response.json()["uuid"]

    # Then update the cluster (mock again for update)
    mock_k8s_client.return_value = mock_client_instance
    response = client.put(
        f"/organizations/{test_environment.organization.uuid}/clusters/{cluster_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "updated-cluster",
            "api_address": "https://k8s-updated.example.com",
            "token": "updated-token-456",
            "environment_uuid": str(test_environment.uuid)
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "updated-cluster"
    assert data["api_address"] == "https://k8s-updated.example.com"


def test_update_cluster_not_found(client, admin_token, test_environment):
    """Test updating non-existent cluster."""
    response = client.put(
        f"/organizations/{test_environment.organization.uuid}/clusters/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "updated-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch('app.clusters.core.cluster_service.K8sClient')
def test_delete_cluster_success(mock_k8s_client, client, admin_token, test_environment):
    """Test successful cluster deletion."""
    # Mock Kubernetes connection validation
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_k8s_client.return_value = mock_client_instance

    # First create a cluster
    create_response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )
    cluster_uuid = create_response.json()["uuid"]

    # Then delete the cluster
    response = client.delete(
        f"/organizations/{test_environment.organization.uuid}/clusters/{cluster_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify cluster is deleted
    get_response = client.get(
        f"/organizations/{test_environment.organization.uuid}/clusters/{cluster_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_cluster_not_found(client, admin_token, test_organization):
    """Test deleting non-existent cluster."""
    response = client.delete(
        f"/organizations/{test_organization.uuid}/clusters/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch('app.clusters.core.cluster_service.K8sClient')
def test_delete_cluster_requires_admin_role(mock_k8s_client, client, admin_token, user_token, test_environment):
    """Test that cluster deletion requires admin role."""
    # Mock Kubernetes connection validation
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
    mock_k8s_client.return_value = mock_client_instance

    # First create a cluster as admin
    create_response = client.post(
        f"/organizations/{test_environment.organization.uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token-123",
            "environment_uuid": str(test_environment.uuid)
        }
    )
    cluster_uuid = create_response.json()["uuid"]

    # Try to delete as regular user
    response = client.delete(
        f"/organizations/{test_environment.organization.uuid}/clusters/{cluster_uuid}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
