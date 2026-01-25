"""
Namespace protection and naming configuration.

This module provides:
1. Configuration for protected namespaces that cannot be used or deleted
2. Namespace naming convention with configurable prefix (default: tron-ns-)
"""

import os
from typing import Set

# Default namespace prefix for all Tron-managed namespaces
DEFAULT_NAMESPACE_PREFIX = "tron-ns-"

# Default Kubernetes system namespaces that should always be protected
DEFAULT_PROTECTED_NAMESPACES = {
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "default",
}


def get_namespace_prefix() -> str:
    """
    Get the namespace prefix for Tron-managed namespaces.

    Configurable via TRON_NAMESPACE_PREFIX environment variable.
    Default: "tron-ns-"

    Returns:
        The namespace prefix string
    """
    return os.getenv("TRON_NAMESPACE_PREFIX", DEFAULT_NAMESPACE_PREFIX)


def get_namespace_for_application(application_name: str) -> str:
    """
    Generate the Kubernetes namespace name for an application.

    All Tron-managed namespaces use a configurable prefix to avoid
    conflicts with existing namespaces in the cluster.

    Args:
        application_name: The application name

    Returns:
        The full namespace name (e.g., "tron-ns-my-app")
    """
    prefix = get_namespace_prefix()
    return f"{prefix}{application_name}"


def get_protected_namespaces() -> Set[str]:
    """
    Get the set of protected namespaces.

    Combines default Kubernetes system namespaces with any additional
    namespaces specified via the PROTECTED_NAMESPACES environment variable.

    Environment variable format: comma-separated list of namespace names
    Example: PROTECTED_NAMESPACES=tron,monitoring,ingress-nginx

    Returns:
        Set of namespace names that are protected
    """
    protected = DEFAULT_PROTECTED_NAMESPACES.copy()

    # Add custom protected namespaces from environment variable
    custom_namespaces = os.getenv("PROTECTED_NAMESPACES", "")
    if custom_namespaces:
        for ns in custom_namespaces.split(","):
            ns = ns.strip()
            if ns:
                protected.add(ns)

    return protected


def is_namespace_protected(namespace: str) -> bool:
    """
    Check if a namespace is protected.

    Args:
        namespace: The namespace name to check

    Returns:
        True if the namespace is protected, False otherwise
    """
    return namespace in get_protected_namespaces()


def is_tron_managed_namespace(namespace: str) -> bool:
    """
    Check if a namespace is managed by Tron (has the Tron prefix).

    Args:
        namespace: The namespace name to check

    Returns:
        True if the namespace is managed by Tron, False otherwise
    """
    prefix = get_namespace_prefix()
    return namespace.startswith(prefix)


class ProtectedNamespaceError(Exception):
    """Raised when an operation is attempted on a protected namespace."""

    def __init__(self, namespace: str, operation: str = "use"):
        self.namespace = namespace
        self.operation = operation
        protected_list = ", ".join(sorted(get_protected_namespaces()))
        self.message = (
            f"Cannot {operation} namespace '{namespace}': it is a protected namespace. "
            f"Protected namespaces: {protected_list}"
        )
        super().__init__(self.message)
