"""Validation and sync context for environment Crossplane config."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

AWS_REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")
AWS_ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")


@dataclass
class CrossplaneContext:
    """Resolved Crossplane configuration for later messaging sync."""

    enabled: bool
    cluster_uuid: UUID | None = None
    aws_region: str | None = None
    aws_account_id: str | None = None
    provider_config: str | None = None
    cluster: Any = None


def validate_crossplane_config(
    enabled: bool,
    cluster_uuid: UUID | None,
    aws_region: str,
    aws_account_id: str,
    provider_config: str,
    environment_id: int,
    get_cluster_by_uuid: Callable[[UUID], Any],
) -> None:
    """Raise ValueError when Crossplane is enabled and catalog config is invalid.

    Catalog rules only (fields + cluster ownership). Live health is validated
    separately on save via ``validate_crossplane_cluster_health``.
    """
    if not enabled:
        return

    if cluster_uuid is None:
        raise ValueError("cluster_uuid is required when Crossplane is enabled")

    region = (aws_region or "").strip()
    if not region:
        raise ValueError("aws_region is required when Crossplane is enabled")
    if not AWS_REGION_PATTERN.match(region):
        raise ValueError(
            "aws_region must be a valid AWS region (e.g. us-east-1, sa-east-1)"
        )

    account_id = (aws_account_id or "").strip()
    if not account_id:
        raise ValueError("aws_account_id is required when Crossplane is enabled")
    if not AWS_ACCOUNT_ID_PATTERN.match(account_id):
        raise ValueError("aws_account_id must be a 12-digit AWS account id")

    config_name = (provider_config or "").strip()
    if not config_name:
        raise ValueError("provider_config is required when Crossplane is enabled")

    cluster = get_cluster_by_uuid(cluster_uuid)
    if not cluster:
        raise ValueError(f"Cluster with UUID {cluster_uuid} not found")
    if cluster.environment_id != environment_id:
        raise ValueError("Crossplane cluster must belong to the same environment")


def validate_crossplane_cluster_health(
    cluster: Any,
    probe_crossplane: Callable[[str, str], dict[str, Any]],
) -> None:
    """Raise ValueError when Crossplane is not installed/healthy on the cluster.

    Called only when enabling Crossplane on an environment (save path), not on
    every sync resolve — so temporary outages do not block catalog reads.
    """
    api_address = getattr(cluster, "api_address", None) or ""
    token = getattr(cluster, "token", None) or ""
    if not api_address or not token:
        raise ValueError(
            "Crossplane cluster is missing api_address or token; cannot verify health"
        )

    status = probe_crossplane(api_address, token)
    available = bool(status.get("available"))
    healthy = bool(status.get("healthy"))
    if available and healthy:
        return

    providers = status.get("providers") or []
    unhealthy = [
        p.get("name", "?")
        for p in providers
        if isinstance(p, dict) and not p.get("healthy")
    ]
    if not available:
        raise ValueError(
            "Crossplane is not available on the selected cluster "
            "(pkg.crossplane.io API group not found)"
        )
    detail = f" unhealthy providers: {', '.join(unhealthy)}" if unhealthy else ""
    raise ValueError(
        "Crossplane is not healthy on the selected cluster"
        f"{detail}. Ensure providers are Healthy before enabling."
    )


def resolve_crossplane_context_for_sync(
    enabled: bool,
    cluster_uuid: UUID | None,
    aws_region: str,
    aws_account_id: str,
    provider_config: str,
    environment_id: int,
    get_cluster_by_uuid: Callable[[UUID], Any],
) -> CrossplaneContext:
    """Resolve Crossplane context for messaging sync."""
    if not enabled:
        return CrossplaneContext(enabled=False)

    validate_crossplane_config(
        enabled,
        cluster_uuid,
        aws_region,
        aws_account_id,
        provider_config,
        environment_id,
        get_cluster_by_uuid,
    )
    cluster = get_cluster_by_uuid(cluster_uuid)
    return CrossplaneContext(
        enabled=True,
        cluster_uuid=cluster_uuid,
        aws_region=aws_region.strip(),
        aws_account_id=aws_account_id.strip(),
        provider_config=provider_config.strip(),
        cluster=cluster,
    )
