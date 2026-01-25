"""
Namespace protection and naming configuration.

This module provides:
1. Configuration for protected namespaces that cannot be used or deleted
2. Namespace naming convention with fixed prefix (tron-ns-)
3. Hardcoded protection to prevent deletion of non-Tron namespaces
"""

import os
from typing import Set

# Fixed namespace prefix for all Tron-managed namespaces
# This is intentionally NOT configurable for security reasons
TRON_NAMESPACE_PREFIX = "tron-ns-"

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

    This is a fixed value (tron-ns-) and is NOT configurable
    for security reasons.

    Returns:
        The namespace prefix string
    """
    return TRON_NAMESPACE_PREFIX


def get_namespace_for_application(application_name: str) -> str:
    """
    Generate the Kubernetes namespace name for an application.

    All Tron-managed namespaces use the fixed prefix 'tron-ns-' to:
    - Avoid conflicts with existing namespaces in the cluster
    - Ensure Tron can only manage its own namespaces
    - Prevent accidental deletion of system or user namespaces

    Args:
        application_name: The application name

    Returns:
        The full namespace name (e.g., "tron-ns-my-app")
    """
    return f"{TRON_NAMESPACE_PREFIX}{application_name}"


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
    Check if a namespace is managed by Tron (has the tron-ns- prefix).

    This is a critical security check - Tron can ONLY delete namespaces
    that it created (i.e., namespaces with the tron-ns- prefix).

    Args:
        namespace: The namespace name to check

    Returns:
        True if the namespace is managed by Tron, False otherwise
    """
    return namespace.startswith(TRON_NAMESPACE_PREFIX)


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


class NotTronManagedNamespaceError(Exception):
    """Raised when trying to delete a namespace not managed by Tron."""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self.message = (
            f"Cannot delete namespace '{namespace}': it is not managed by Tron. "
            f"Tron can only delete namespaces with the '{TRON_NAMESPACE_PREFIX}' prefix."
        )
        super().__init__(self.message)
