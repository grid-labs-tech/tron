"""Unit tests for K8sClient.check_crossplane_status."""

from unittest.mock import MagicMock, patch

from kubernetes.client.exceptions import ApiException

from app.k8s.client import K8sClient


def _client() -> K8sClient:
    with patch.object(K8sClient, "__init__", lambda self, url, token, verify_ssl=False: None):
        k8s = K8sClient(url="https://k8s.example.com", token="token")
    k8s.api_client = MagicMock()
    return k8s


def test_check_crossplane_status_not_available():
    k8s = _client()
    with patch.object(k8s, "check_api_available", return_value=False):
        status = k8s.check_crossplane_status()

    assert status == {"available": False, "healthy": False, "providers": []}


def test_check_crossplane_status_healthy_providers():
    k8s = _client()
    mock_custom = MagicMock()
    mock_custom.list_cluster_custom_object.return_value = {
        "items": [
            {
                "metadata": {"name": "provider-aws-sqs"},
                "status": {
                    "conditions": [{"type": "Healthy", "status": "True"}],
                },
            },
            {
                "metadata": {"name": "provider-aws-sns"},
                "status": {
                    "conditions": [{"type": "Healthy", "status": "True"}],
                },
            },
        ]
    }

    with (
        patch.object(k8s, "check_api_available", return_value=True),
        patch("app.k8s.client.client.CustomObjectsApi", return_value=mock_custom),
    ):
        status = k8s.check_crossplane_status()

    assert status["available"] is True
    assert status["healthy"] is True
    assert len(status["providers"]) == 2
    assert all(p["healthy"] for p in status["providers"])


def test_check_crossplane_status_unhealthy_provider():
    k8s = _client()
    mock_custom = MagicMock()
    mock_custom.list_cluster_custom_object.return_value = {
        "items": [
            {
                "metadata": {"name": "provider-aws-sqs"},
                "status": {
                    "conditions": [{"type": "Healthy", "status": "False"}],
                },
            },
        ]
    }

    with (
        patch.object(k8s, "check_api_available", return_value=True),
        patch("app.k8s.client.client.CustomObjectsApi", return_value=mock_custom),
    ):
        status = k8s.check_crossplane_status()

    assert status["available"] is True
    assert status["healthy"] is False
    assert status["providers"] == [{"name": "provider-aws-sqs", "healthy": False}]


def test_check_crossplane_status_no_providers():
    k8s = _client()
    mock_custom = MagicMock()
    mock_custom.list_cluster_custom_object.return_value = {"items": []}

    with (
        patch.object(k8s, "check_api_available", return_value=True),
        patch("app.k8s.client.client.CustomObjectsApi", return_value=mock_custom),
    ):
        status = k8s.check_crossplane_status()

    assert status["available"] is True
    assert status["healthy"] is False
    assert status["providers"] == []


def test_check_crossplane_status_list_error():
    k8s = _client()
    mock_custom = MagicMock()
    mock_custom.list_cluster_custom_object.side_effect = ApiException(status=403)

    with (
        patch.object(k8s, "check_api_available", return_value=True),
        patch("app.k8s.client.client.CustomObjectsApi", return_value=mock_custom),
    ):
        status = k8s.check_crossplane_status()

    assert status == {"available": True, "healthy": False, "providers": []}
