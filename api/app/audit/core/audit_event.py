"""Audit event schema and HTTP method to action mapping."""

from datetime import datetime, timezone


def map_method_to_action(method: str, path: str) -> str:
    """
    Map HTTP method and path to audit action.
    GET=READ, POST=CREATE/EXEC, PUT/PATCH=UPDATE, DELETE=DELETE.
    For /exec endpoints, use EXEC.
    """
    method_upper = method.upper()
    path_lower = path.lower()

    if "/exec" in path_lower:
        return "EXEC"

    mapping = {
        "GET": "READ",
        "HEAD": "READ",
        "OPTIONS": "READ",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }
    return mapping.get(method_upper, "UNKNOWN")


def normalize_resource(path: str) -> str:
    """
    Normalize request path to resource identifier.
    Strips leading slash and collapses repeated slashes.
    Keeps path structure (e.g., organizations/123/instances/456).
    """
    if not path:
        return "unknown"
    # Remove leading slash, strip trailing slash
    normalized = path.strip("/")
    # Collapse multiple slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized or "unknown"


def _truncate_for_audit(value: str, max_length: int = 4096) -> str:
    """Truncate string for audit logging to avoid huge payloads."""
    if not value or len(value) <= max_length:
        return value
    return value[:max_length] + f"... [truncated, total {len(value)} chars]"


def build_audit_event(
    actor: str,
    method: str,
    path: str,
    status_code: int,
    source_ip: str,
    exec_payload: dict | None = None,
) -> dict:
    """Build an audit event dict from request/response data."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": map_method_to_action(method, path),
        "resource": normalize_resource(path),
        "status": f"{'success' if 200 <= status_code < 400 else 'failure'}:{status_code}",
        "source_ip": source_ip,
    }
    if exec_payload:
        event["exec_request"] = exec_payload.get("request")
        response_data = exec_payload.get("response")
        if response_data and isinstance(response_data, dict):
            truncated = response_data.copy()
            if "stdout" in truncated and isinstance(truncated["stdout"], str):
                truncated["stdout"] = _truncate_for_audit(truncated["stdout"])
            if "stderr" in truncated and isinstance(truncated["stderr"], str):
                truncated["stderr"] = _truncate_for_audit(truncated["stderr"])
            event["exec_response"] = truncated
        else:
            event["exec_response"] = response_data
    return event
