
import pytest
from unittest.mock import MagicMock
from app.helpers.serializers import serialize_webapp_deploy

def test_serialize_webapp_deploy():

    mock_webapp_deploy = MagicMock()

    mock_webapp_deploy.webapp.name = "test-webapp"
    mock_webapp_deploy.webapp.uuid = "123e4567-e89b-12d3-a456-426614174000"
    mock_webapp_deploy.webapp.namespace.name = "test-namespace"
    mock_webapp_deploy.webapp.namespace.uuid = "123e4567-e89b-12d3-a456-426614174111"
    mock_webapp_deploy.environment.name = "staging"
    mock_webapp_deploy.workload.name = "general"
    mock_webapp_deploy.image = "nginx"
    mock_webapp_deploy.version = "1.0.0"
    mock_webapp_deploy.cpu_scaling_threshold = 80
    mock_webapp_deploy.memory_scaling_threshold = 70
    mock_webapp_deploy.envs = [{"chave": "valor"}]
    mock_webapp_deploy.secrets = []
    mock_webapp_deploy.custom_metrics = {"enabled": False, "path": "/metrics", "port": 8080}
    mock_webapp_deploy.healthcheck = {"path": "/healthcheck","protocol": "http","port": 80,"timeout": 5,"interval": 31,"initial_interval": 30,"failure_threshold": 2}
    mock_webapp_deploy.endpoints = [{"source_protocol": "http","source_port": 80,"dest_protocol": "http","dest_port": 80}]
    mock_webapp_deploy.cpu = "0.25"
    mock_webapp_deploy.memory = 128

    result = serialize_webapp_deploy(mock_webapp_deploy)

    expected_result = {
        "webapp_name": "test-webapp",
        "webapp_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "namespace_name": "test-namespace",
        "namespace_uuid": "123e4567-e89b-12d3-a456-426614174111",
        "environment": "staging",
        "workload": "general",
        "image": "nginx",
        "version": "1.0.0",
        "cpu_scaling_threshold": 80,
        "memory_scaling_threshold": 70,
        "envs": [{"chave": "valor"}],
        "secrets": [],
        "custom_metrics": {"enabled": False, "path": "/metrics", "port": 8080},
        "healthcheck": {"path": "/healthcheck","protocol": "http","port": 80,"timeout": 5,"interval": 31,"initial_interval": 30,"failure_threshold": 2},
        "endpoints": [{"source_protocol": "http","source_port": 80,"dest_protocol": "http","dest_port": 80}],
        "cpu": "0.25",
        "memory": 128
    }

    assert result == expected_result
