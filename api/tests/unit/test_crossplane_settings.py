"""Unit tests for environment Crossplane config validation."""
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.crossplane.core.crossplane_validators import (
    resolve_crossplane_context_for_sync,
    validate_crossplane_cluster_health,
    validate_crossplane_config,
)
from app.environments.core.environment_settings_defaults import (
    merge_missing_default_settings,
)


def _cluster(environment_id: int):
    cluster = MagicMock()
    cluster.environment_id = environment_id
    cluster.uuid = uuid4()
    return cluster


def test_validate_disabled_requires_no_fields():
    validate_crossplane_config(
        enabled=False,
        cluster_uuid=None,
        aws_region="",
        aws_account_id="",
        provider_config="",
        environment_id=1,
        get_cluster_by_uuid=lambda _: None,
    )


def test_validate_enabled_missing_provider_config():
    with pytest.raises(ValueError, match="provider_config"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=uuid4(),
            aws_region="us-east-1",
            aws_account_id="000000000000",
            provider_config="",
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_missing_aws_account_id():
    with pytest.raises(ValueError, match="aws_account_id"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=uuid4(),
            aws_region="us-east-1",
            aws_account_id="",
            provider_config="default",
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_invalid_aws_account_id():
    with pytest.raises(ValueError, match="aws_account_id"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=uuid4(),
            aws_region="us-east-1",
            aws_account_id="not-valid",
            provider_config="default",
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_missing_cluster_uuid():
    with pytest.raises(ValueError, match="cluster_uuid"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=None,
            aws_region="us-east-1",
            aws_account_id="000000000000",
            provider_config="floci",
            environment_id=1,
            get_cluster_by_uuid=lambda _: None,
        )


def test_validate_enabled_invalid_aws_region():
    with pytest.raises(ValueError, match="aws_region"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=uuid4(),
            aws_region="invalid",
            aws_account_id="000000000000",
            provider_config="floci",
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_cluster_not_found():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match="not found"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=cluster_uuid,
            aws_region="us-east-1",
            aws_account_id="000000000000",
            provider_config="floci",
            environment_id=1,
            get_cluster_by_uuid=lambda _: None,
        )


def test_validate_enabled_cluster_wrong_environment():
    with pytest.raises(ValueError, match="same environment"):
        validate_crossplane_config(
            enabled=True,
            cluster_uuid=uuid4(),
            aws_region="us-east-1",
            aws_account_id="000000000000",
            provider_config="floci",
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(environment_id=2),
        )


def test_validate_cluster_health_ok():
    cluster = _cluster(1)
    cluster.api_address = "https://k8s.example.com"
    cluster.token = "token"
    validate_crossplane_cluster_health(
        cluster,
        probe_crossplane=lambda *_: {
            "available": True,
            "healthy": True,
            "providers": [{"name": "provider-aws-sqs", "healthy": True}],
        },
    )


def test_validate_cluster_health_not_available():
    cluster = _cluster(1)
    cluster.api_address = "https://k8s.example.com"
    cluster.token = "token"
    with pytest.raises(ValueError, match="not available"):
        validate_crossplane_cluster_health(
            cluster,
            probe_crossplane=lambda *_: {
                "available": False,
                "healthy": False,
                "providers": [],
            },
        )


def test_validate_cluster_health_unhealthy_providers():
    cluster = _cluster(1)
    cluster.api_address = "https://k8s.example.com"
    cluster.token = "token"
    with pytest.raises(ValueError, match="not healthy"):
        validate_crossplane_cluster_health(
            cluster,
            probe_crossplane=lambda *_: {
                "available": True,
                "healthy": False,
                "providers": [{"name": "provider-aws-sqs", "healthy": False}],
            },
        )


def test_resolve_disabled_context():
    ctx = resolve_crossplane_context_for_sync(
        enabled=False,
        cluster_uuid=None,
        aws_region="",
        aws_account_id="",
        provider_config="",
        environment_id=1,
        get_cluster_by_uuid=lambda _: None,
    )
    assert ctx.enabled is False
    assert ctx.cluster is None


def test_resolve_enabled_context():
    cluster_uuid = uuid4()
    cluster = _cluster(environment_id=5)
    cluster.uuid = cluster_uuid

    ctx = resolve_crossplane_context_for_sync(
        enabled=True,
        cluster_uuid=cluster_uuid,
        aws_region="us-east-1",
        aws_account_id="310090716792",
        provider_config="floci",
        environment_id=5,
        get_cluster_by_uuid=lambda uid: cluster if uid == cluster_uuid else None,
    )

    assert ctx.enabled is True
    assert ctx.cluster_uuid == cluster_uuid
    assert ctx.aws_region == "us-east-1"
    assert ctx.aws_account_id == "310090716792"
    assert ctx.provider_config == "floci"
    assert ctx.cluster is cluster


def test_merge_missing_default_settings_does_not_include_crossplane_keys():
    merged = merge_missing_default_settings(
        [{"key": "max_pods", "value": 5, "description": "", "type": "number"}]
    )
    keys = {item["key"] for item in merged}
    assert "crossplane_enabled" not in keys
    assert "crossplane_cluster_uuid" not in keys
    assert "crossplane_aws_region" not in keys
    assert "crossplane_provider_config" not in keys
    assert "max_pods" in keys
    assert "min_cpu_cores" in keys
