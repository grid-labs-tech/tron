"""
Namespace protection configuration.

This module provides configuration for protected namespaces that cannot be
used for applications or deleted by the platform.
"""

import os
from typing import Set

# Default Kubernetes system namespaces that should always be protected
DEFAULT_PROTECTED_NAMESPACES = {
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "default",
}


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
