"""Tests for namespace protection and naming functionality."""

import os
import pytest
from unittest.mock import patch

from app.shared.config.namespace_protection import (
    get_protected_namespaces,
    is_namespace_protected,
    is_tron_managed_namespace,
    get_namespace_for_application,
    get_namespace_prefix,
    ProtectedNamespaceError,
    DEFAULT_PROTECTED_NAMESPACES,
    DEFAULT_NAMESPACE_PREFIX,
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


class TestGetNamespacePrefix:
    """Tests for get_namespace_prefix function."""

    def test_returns_default_prefix(self):
        """Should return default prefix when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_namespace_prefix() == DEFAULT_NAMESPACE_PREFIX

    def test_returns_custom_prefix_from_env(self):
        """Should return custom prefix from environment variable."""
        with patch.dict(os.environ, {"TRON_NAMESPACE_PREFIX": "custom-"}):
            assert get_namespace_prefix() == "custom-"


class TestGetNamespaceForApplication:
    """Tests for get_namespace_for_application function."""

    def test_adds_default_prefix(self):
        """Should add default prefix to application name."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_namespace_for_application("my-app")
            assert result == "tron-ns-my-app"

    def test_adds_custom_prefix(self):
        """Should add custom prefix when configured."""
        with patch.dict(os.environ, {"TRON_NAMESPACE_PREFIX": "prod-"}):
            result = get_namespace_for_application("api")
            assert result == "prod-api"

    def test_handles_empty_app_name(self):
        """Should handle empty application name."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_namespace_for_application("")
            assert result == "tron-ns-"


class TestIsTronManagedNamespace:
    """Tests for is_tron_managed_namespace function."""

    def test_detects_tron_managed_namespace(self):
        """Should detect namespaces with Tron prefix."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_tron_managed_namespace("tron-ns-my-app") is True
            assert is_tron_managed_namespace("tron-ns-api") is True

    def test_rejects_non_tron_namespace(self):
        """Should reject namespaces without Tron prefix."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_tron_managed_namespace("kube-system") is False
            assert is_tron_managed_namespace("my-app") is False
            assert is_tron_managed_namespace("default") is False

    def test_uses_custom_prefix(self):
        """Should use custom prefix when configured."""
        with patch.dict(os.environ, {"TRON_NAMESPACE_PREFIX": "custom-"}):
            assert is_tron_managed_namespace("custom-my-app") is True
            assert is_tron_managed_namespace("tron-ns-my-app") is False
