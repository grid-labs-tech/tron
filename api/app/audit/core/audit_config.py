"""Audit logging configuration loaded from environment variables."""

import os


def is_audit_enabled() -> bool:
    """Return True if audit logging is enabled via AUDIT_LOG_ENABLED."""
    return os.getenv("AUDIT_LOG_ENABLED", "false").lower() == "true"


def get_siem_url() -> str | None:
    """Return the SIEM endpoint URL or None if not configured."""
    return os.getenv("AUDIT_SIEM_URL") or None


def get_siem_token() -> str | None:
    """Return the SIEM Bearer token or None if not configured."""
    return os.getenv("AUDIT_SIEM_TOKEN") or None


def get_siem_timeout() -> float:
    """Return the SIEM HTTP timeout in seconds (default: 5)."""
    try:
        return float(os.getenv("AUDIT_SIEM_TIMEOUT", "5"))
    except ValueError:
        return 5.0
