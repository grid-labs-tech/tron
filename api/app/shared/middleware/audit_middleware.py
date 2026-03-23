"""Audit logging middleware - captures request/response and sends to SIEM."""

import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.audit.core.audit_config import get_siem_url
from app.audit.core.audit_event import build_audit_event
from app.audit.core.audit_sender import send_audit_event

SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def _get_client_ip(request: Request) -> str:
    """Extract client IP, supporting X-Forwarded-For and X-Real-IP proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs audit events to configured SIEM endpoint."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if path in SKIP_PATHS:
            return response

        siem_url = get_siem_url()
        if not siem_url:
            return response

        actor = getattr(request.state, "audit_actor", None) or "anonymous"
        source_ip = _get_client_ip(request)
        exec_payload = getattr(request.state, "audit_exec_payload", None)

        event = build_audit_event(
            actor=actor,
            method=request.method,
            path=path,
            status_code=response.status_code,
            source_ip=source_ip,
            exec_payload=exec_payload,
        )

        task = asyncio.create_task(send_audit_event(siem_url, event))

        def _log_task_error(t):
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                import logging

                logging.getLogger(__name__).warning(
                    "Audit task failed: %s", exc, exc_info=True
                )

        task.add_done_callback(_log_task_error)

        return response
