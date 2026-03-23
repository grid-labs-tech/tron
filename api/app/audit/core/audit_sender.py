"""Asynchronous audit event sender with fail-open behavior."""

import logging
from typing import Any

import httpx
from httpx import ConnectError, TimeoutException

from app.audit.core.audit_config import get_siem_token, get_siem_timeout

logger = logging.getLogger(__name__)


async def send_audit_event(siem_url: str, payload: dict[str, Any]) -> None:
    """
    Send audit event to SIEM endpoint asynchronously.
    Fail-open: logs errors but never propagates exceptions.
    """
    timeout = get_siem_timeout()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = get_siem_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                siem_url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if response.status_code >= 400:
                logger.warning(
                    "Audit SIEM returned %s for event: %s",
                    response.status_code,
                    payload.get("resource", "unknown"),
                )
    except TimeoutException as e:
        logger.warning("Audit SIEM request timed out: %s", e)
    except ConnectError as e:
        logger.warning("Audit SIEM request failed: %s", e)
    except httpx.RequestError as e:
        logger.warning("Audit SIEM request failed: %s", e)
    except Exception as e:
        logger.warning("Audit send unexpected error: %s", e)
