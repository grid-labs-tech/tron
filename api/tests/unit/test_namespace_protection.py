"""Tests for namespace protection functionality."""

import os
import pytest
from unittest.mock import patch

from app.shared.config.namespace_protection import (
    get_protected_namespaces,
    is_namespace_protected,
    ProtectedNamespaceError,
    DEFAULT_PROTECTED_NAMESPACES,
)
from app.applications.core.application_validators import (
    validate_application_name_not_protected,
    ApplicationNameProtectedError,
)


class TestGetProtectedNamespaces:
    """Tests for get_protected_namespaces function."""

    def test_returns_default_namespaces(self):
        """Should return default protected namespaces."""
        with patch.dict(os.environ, {}, clear=True):
            namespaces = get_protected_namespaces()
            assert "kube-system" in namespaces
            assert "kube-public" in namespaces
            assert "kube-node-lease" in namespaces
            assert "default" in namespaces

    def test_includes_custom_namespaces_from_env(self):
        """Should include custom namespaces from environment variable."""
        with patch.dict(os.environ, {"PROTECTED_NAMESPACES": "tron,monitoring"}):
            namespaces = get_protected_namespaces()
            assert "tron" in namespaces
            assert "monitoring" in namespaces
            # Default should still be included
            assert "kube-system" in namespaces

    def test_handles_spaces_in_custom_namespaces(self):
        """Should handle spaces around namespace names."""
        with patch.dict(os.environ, {"PROTECTED_NAMESPACES": " tron , monitoring "}):
            namespaces = get_protected_namespaces()
            assert "tron" in namespaces
            assert "monitoring" in namespaces

    def test_handles_empty_env_variable(self):
        """Should handle empty environment variable."""
        with patch.dict(os.environ, {"PROTECTED_NAMESPACES": ""}):
            namespaces = get_protected_namespaces()
            # Should only have default namespaces
            assert namespaces == DEFAULT_PROTECTED_NAMESPACES


class TestIsNamespaceProtected:
    """Tests for is_namespace_protected function."""

    def test_default_namespaces_are_protected(self):
        """Default Kubernetes namespaces should be protected."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_namespace_protected("kube-system") is True
            assert is_namespace_protected("kube-public") is True
            assert is_namespace_protected("default") is True

    def test_custom_namespace_not_protected_by_default(self):
        """Custom namespaces should not be protected by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_namespace_protected("my-app") is False
            assert is_namespace_protected("tron") is False

    def test_custom_namespace_protected_when_configured(self):
        """Custom namespaces should be protected when configured."""
        with patch.dict(os.environ, {"PROTECTED_NAMESPACES": "tron,monitoring"}):
            assert is_namespace_protected("tron") is True
            assert is_namespace_protected("monitoring") is True
            assert is_namespace_protected("other-app") is False


class TestProtectedNamespaceError:
    """Tests for ProtectedNamespaceError exception."""

    def test_error_message_includes_namespace(self):
        """Error message should include the namespace name."""
        error = ProtectedNamespaceError("kube-system", "delete")
        assert "kube-system" in str(error)
        assert "delete" in str(error)

    def test_error_message_lists_protected_namespaces(self):
        """Error message should list protected namespaces."""
        with patch.dict(os.environ, {}, clear=True):
            error = ProtectedNamespaceError("kube-system", "use")
            assert "kube-system" in error.message


class TestValidateApplicationNameNotProtected:
    """Tests for validate_application_name_not_protected function."""

    def test_raises_error_for_protected_namespace(self):
        """Should raise error when name matches protected namespace."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ApplicationNameProtectedError):
                validate_application_name_not_protected("kube-system")

    def test_allows_non_protected_names(self):
        """Should not raise error for non-protected names."""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise
            validate_application_name_not_protected("my-app")
            validate_application_name_not_protected("production-api")

    def test_raises_error_for_custom_protected_namespace(self):
        """Should raise error for custom protected namespaces."""
        with patch.dict(os.environ, {"PROTECTED_NAMESPACES": "tron"}):
            with pytest.raises(ApplicationNameProtectedError):
                validate_application_name_not_protected("tron")
