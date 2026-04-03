"""Tests for graph_failure_context."""

from unittest.mock import MagicMock

from azure.core.exceptions import HttpResponseError

from m365_posture.graph_errors import graph_failure_context


def test_graph_failure_context_http_response_error_includes_request_id_from_header() -> None:
    response = MagicMock()
    response.status_code = 404
    response.headers = {
        "request-id": "graph-req-abc",
        "client-request-id": "client-xyz",
    }
    response.json.return_value = {
        "error": {
            "code": "ResourceNotFound",
            "message": "Not found",
            "access_token": "should-not-appear",
        }
    }

    exc = HttpResponseError(response=response)
    ctx = graph_failure_context(exc, operation="list_users")

    assert ctx["operation"] == "list_users"
    assert ctx["error_type"] == "HttpResponseError"
    assert "request_id" in ctx
    assert ctx["request_id"] == "graph-req-abc"
    assert ctx.get("client_request_id") == "client-xyz"
    assert ctx["http_status"] == 404
    body = ctx.get("graph_body")
    assert isinstance(body, dict)
    err = body.get("error", {})
    assert err.get("access_token") == "[REDACTED]"


def test_graph_failure_context_generic_exception() -> None:
    ctx = graph_failure_context(ValueError("nope"), operation="ping")
    assert ctx["operation"] == "ping"
    assert ctx["error_type"] == "ValueError"
    assert ctx["message"] == "nope"
    assert "http_status" not in ctx
