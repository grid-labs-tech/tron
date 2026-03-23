"""Unit tests for audit sender - fail-open behavior."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.audit.core.audit_sender import send_audit_event


def _run(coro):
    """Run async coroutine in sync test."""
    return asyncio.run(coro)


def test_send_audit_event_success():
    """Should complete without raising when SIEM accepts the event."""
    with patch("app.audit.core.audit_sender.httpx") as mock_httpx:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client

        _run(send_audit_event("https://siem.example.com/ingest", {"actor": "test"}))

        mock_client.post.assert_called_once()


def test_send_audit_event_timeout_fail_open():
    """Should not raise when SIEM times out (fail-open)."""
    from httpx import TimeoutException

    with patch("app.audit.core.audit_sender.httpx") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client

        _run(send_audit_event("https://siem.example.com/ingest", {"actor": "test"}))

        # No exception propagated
        mock_client.post.assert_called_once()


def test_send_audit_event_connection_error_fail_open():
    """Should not raise when SIEM is unreachable (fail-open)."""
    from httpx import ConnectError

    with patch("app.audit.core.audit_sender.httpx") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=ConnectError("unreachable"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client

        _run(send_audit_event("https://siem.example.com/ingest", {"actor": "test"}))

        # No exception propagated
        mock_client.post.assert_called_once()
