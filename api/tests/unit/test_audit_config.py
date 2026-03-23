"""Unit tests for audit configuration."""

import os
from unittest.mock import patch

from app.audit.core.audit_config import (
    is_audit_enabled,
    get_siem_url,
    get_siem_token,
    get_siem_timeout,
)


class TestIsAuditEnabled:
    """Tests for is_audit_enabled."""

    def test_default_is_false(self):
        with patch.dict(os.environ, {}, clear=True):
            assert is_audit_enabled() is False

    def test_true_when_enabled(self):
        with patch.dict(os.environ, {"AUDIT_LOG_ENABLED": "true"}):
            assert is_audit_enabled() is True

    def test_case_insensitive_true(self):
        with patch.dict(os.environ, {"AUDIT_LOG_ENABLED": "TRUE"}):
            assert is_audit_enabled() is True


class TestGetSiemUrl:
    """Tests for get_siem_url."""

    def test_returns_none_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_siem_url() is None

    def test_returns_url_when_set(self):
        with patch.dict(os.environ, {"AUDIT_SIEM_URL": "https://logs.example.com/ingest"}):
            assert get_siem_url() == "https://logs.example.com/ingest"


class TestGetSiemToken:
    """Tests for get_siem_token."""

    def test_returns_none_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_siem_token() is None

    def test_returns_token_when_set(self):
        with patch.dict(os.environ, {"AUDIT_SIEM_TOKEN": "secret-token"}):
            assert get_siem_token() == "secret-token"


class TestGetSiemTimeout:
    """Tests for get_siem_timeout."""

    def test_default_is_five(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_siem_timeout() == 5.0

    def test_parses_custom_timeout(self):
        with patch.dict(os.environ, {"AUDIT_SIEM_TIMEOUT": "10"}):
            assert get_siem_timeout() == 10.0

    def test_invalid_falls_back_to_five(self):
        with patch.dict(os.environ, {"AUDIT_SIEM_TIMEOUT": "invalid"}):
            assert get_siem_timeout() == 5.0
