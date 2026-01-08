import pytest
from unittest.mock import patch, MagicMock
from app.services.kubernetes.application_component_manager import (
    KubernetesApplicationComponentManager,
)


def test_instance_management():

    webapp_deploy_serialized = {
        "webapp_name": "teste",
        "webapp_uuid": "4329360f-19fe-4674-813f-4ab7146ac0b3",
        "namespace_name": "teste-namespace",
        "namespace_uuid": "a8ef62c3-2860-461e-ad74-dc1472691f2d",
        "environment": "staging",
        "workload": "general",
        "image": "nginx",
        "version": "1.0.0",
        "cpu_scaling_threshold": 80,
        "memory_scaling_threshold": 80,
        "envs": [{"key", "value"}],
        "secrets": [],
        "custom_metrics": {"enabled": False, "path": "/metrics", "port": 0},
        "healthcheck": {
            "path": "/healthcheck",
            "protocol": "http",
            "port": 80,
            "timeout": 5,
            "interval": 31,
            "initial_interval": 30,
            "failure_threshold": 2,
        },
        "endpoints": [
            {
                "source_protocol": "http",
                "source_port": 80,
                "dest_protocol": "http",
                "dest_port": 80,
            }
        ],
        "cpu": 0.25,
        "memory": 128
    }

    # Mock database session
    mock_db = MagicMock()

    # Mock templates
    mock_template = MagicMock()
    mock_template.content = "kind: Deployment\napiVersion: apps/v1\nmetadata:\n  name: test"
    mock_template.name = "test-template"

    with patch('app.services.component_template_config.ComponentTemplateConfigService.get_templates_for_component', return_value=[mock_template]):
        kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
            webapp_deploy_serialized, "webapp", db=mock_db
        )

    kinds = []
    api_versions = []

    for item in kubernetes_payload:
        kinds.append(item.get("kind"))
        api_versions.append(item.get("apiVersion"))

    assert len(kubernetes_payload) == 3
    assert kinds == ["Deployment", "HorizontalPodAutoscaler", "Service"]
    assert api_versions == ["apps/v1", "autoscaling/v2", "v1"]
