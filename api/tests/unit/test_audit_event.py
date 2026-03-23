"""Unit tests for audit event schema and mapping."""


from app.audit.core.audit_event import (
    map_method_to_action,
    normalize_resource,
    build_audit_event,
)


class TestMapMethodToAction:
    """Tests for HTTP method to audit action mapping."""

    def test_get_maps_to_read(self):
        assert map_method_to_action("GET", "/instances") == "READ"

    def test_head_maps_to_read(self):
        assert map_method_to_action("HEAD", "/health") == "READ"

    def test_post_maps_to_create(self):
        assert map_method_to_action("POST", "/instances") == "CREATE"

    def test_put_maps_to_update(self):
        assert map_method_to_action("PUT", "/instances/123") == "UPDATE"

    def test_patch_maps_to_update(self):
        assert map_method_to_action("PATCH", "/instances/123") == "UPDATE"

    def test_delete_maps_to_delete(self):
        assert map_method_to_action("DELETE", "/instances/123") == "DELETE"

    def test_exec_path_maps_to_exec(self):
        assert map_method_to_action("POST", "/workers/abc/pods/x/exec") == "EXEC"

    def test_exec_path_case_insensitive(self):
        assert map_method_to_action("POST", "/webapps/abc/pods/x/EXEC") == "EXEC"

    def test_unknown_method_maps_to_unknown(self):
        assert map_method_to_action("TRACE", "/instances") == "UNKNOWN"


class TestNormalizeResource:
    """Tests for path to resource normalization."""

    def test_strips_leading_slash(self):
        assert normalize_resource("/instances") == "instances"

    def test_strips_trailing_slash(self):
        assert normalize_resource("instances/") == "instances"

    def test_preserves_path_structure(self):
        assert normalize_resource("/organizations/123/instances/456") == "organizations/123/instances/456"

    def test_empty_path_returns_unknown(self):
        assert normalize_resource("") == "unknown"

    def test_slash_only_returns_unknown(self):
        assert normalize_resource("/") == "unknown"

    def test_collapses_double_slashes(self):
        assert normalize_resource("/orgs//instances") == "orgs/instances"


class TestBuildAuditEvent:
    """Tests for build_audit_event."""

    def test_builds_valid_event(self):
        event = build_audit_event(
            actor="user@example.com",
            method="GET",
            path="/instances",
            status_code=200,
            source_ip="192.168.1.1",
        )
        assert isinstance(event, dict)
        assert event["actor"] == "user@example.com"
        assert event["action"] == "READ"
        assert event["resource"] == "instances"
        assert event["status"] == "success:200"
        assert event["source_ip"] == "192.168.1.1"
        assert "T" in event["timestamp"]  # ISO format

    def test_failure_status(self):
        event = build_audit_event(
            actor="anonymous",
            method="POST",
            path="/auth/login",
            status_code=401,
            source_ip="10.0.0.1",
        )
        assert event["status"] == "failure:401"

    def test_exec_payload_included(self):
        event = build_audit_event(
            actor="admin@example.com",
            method="POST",
            path="/workers/abc/pods/x/exec",
            status_code=200,
            source_ip="10.0.0.1",
            exec_payload={
                "request": {"command": ["ls", "-la"], "container_name": "app"},
                "response": {
                    "stdout": "total 4\ndrwxr-xr-x",
                    "stderr": "",
                    "return_code": 0,
                },
            },
        )
        assert event["action"] == "EXEC"
        assert event["exec_request"] == {"command": ["ls", "-la"], "container_name": "app"}
        assert event["exec_response"]["stdout"] == "total 4\ndrwxr-xr-x"
        assert event["exec_response"]["return_code"] == 0

    def test_exec_response_truncated_for_large_output(self):
        long_stdout = "x" * 5000
        event = build_audit_event(
            actor="user@example.com",
            method="POST",
            path="/webapps/abc/pods/x/exec",
            status_code=200,
            source_ip="10.0.0.1",
            exec_payload={
                "request": {"command": ["cat", "huge.log"], "container_name": None},
                "response": {"stdout": long_stdout, "stderr": "", "return_code": 0},
            },
        )
        assert len(event["exec_response"]["stdout"]) < 5000
        assert "truncated" in event["exec_response"]["stdout"]
