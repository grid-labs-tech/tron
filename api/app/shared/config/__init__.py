from app.shared.config.namespace_protection import (
    get_protected_namespaces,
    is_namespace_protected,
    is_tron_managed_namespace,
    get_namespace_for_application,
    get_namespace_prefix,
    ProtectedNamespaceError,
    NotTronManagedNamespaceError,
    DEFAULT_PROTECTED_NAMESPACES,
    TRON_NAMESPACE_PREFIX,
)

__all__ = [
    "get_protected_namespaces",
    "is_namespace_protected",
    "is_tron_managed_namespace",
    "get_namespace_for_application",
    "get_namespace_prefix",
    "ProtectedNamespaceError",
    "NotTronManagedNamespaceError",
    "DEFAULT_PROTECTED_NAMESPACES",
    "TRON_NAMESPACE_PREFIX",
]
