"""Adapter: probe Crossplane health on a Kubernetes cluster.

Belongs to the Crossplane bounded context infra layer. Uses shared K8sClient
as a technical dependency (same pattern as messaging sync), without importing
the clusters application service.
"""

from __future__ import annotations

from typing import Any

from app.k8s.client import K8sClient


def probe_crossplane_health(api_address: str, token: str) -> dict[str, Any]:
    """
    Live-check Crossplane on the given cluster credentials.

    Returns the same shape as K8sClient.check_crossplane_status:
    {available, healthy, providers: [{name, healthy}, ...]}.

    When the API is unreachable, returns available=False / healthy=False.
    """
    k8s_client = K8sClient(url=api_address, token=token)
    success, _detail = k8s_client.validate_connection()
    if not success:
        return {"available": False, "healthy": False, "providers": []}
    return k8s_client.check_crossplane_status()
