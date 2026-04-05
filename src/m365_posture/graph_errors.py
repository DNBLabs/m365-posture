"""Convert exceptions and HTTP responses into log-safe diagnostic dictionaries.

Strips tokens, secrets, and PEM material from payloads before they are written to
log files. Correlation headers (``request-id``, ``client-request-id``) are preserved
for Microsoft support and tenant troubleshooting.
"""

from __future__ import annotations

import re
from typing import Any

try:
    from azure.core.exceptions import HttpResponseError as _HttpResponseError
except ImportError:  # pragma: no cover - azure-core is a transitive dependency
    _HttpResponseError = None

_SENSITIVE_KEY_FRAGMENTS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "assertion",
    "password",
    "private_key",
    "client_assertion",
)
_SENSITIVE_KEYS = frozenset(_SENSITIVE_KEY_FRAGMENTS)

_PEM_BEGIN = re.compile(r"-----BEGIN [^-]+-----", re.IGNORECASE)


def _header_get(headers: Any, *names: str) -> str | None:
    """Read the first present header value from a case-insensitive set of names.

    Graph and Azure SDK responses use inconsistent header casing; this tries
    several variants per logical name.

    Args:
        headers: Mapping-like headers object, or ``None``.
        names: Preferred header names to try in order.

    Returns:
        First non-empty string value, or ``None``.
    """
    if headers is None:
        return None
    for name in names:
        for key in (name, name.lower(), name.upper()):
            val = headers.get(key) if hasattr(headers, "get") else None
            if val:
                return str(val)
    return None


def _is_sensitive_key(key: str) -> bool:
    """Return True if a JSON key name suggests secret or credential material.

    Args:
        key: Object key from a parsed body or dict.

    Returns:
        ``True`` if the key should be redacted in logs.
    """
    kl = key.lower().replace(" ", "_").replace("-", "_")
    if kl in _SENSITIVE_KEYS:
        return True
    return any(frag in kl for frag in _SENSITIVE_KEY_FRAGMENTS)


def _sanitize_scalar(val: Any) -> Any:
    """Redact bearer tokens and PEM blocks embedded in string scalars.

    Args:
        val: Any value; non-strings are returned unchanged.

    Returns:
        Redacted string or the original non-string value.
    """
    if not isinstance(val, str):
        return val
    if _PEM_BEGIN.search(val):
        return "[REDACTED:PEM_OR_KEY_MATERIAL]"
    if val.lower().startswith("bearer ") and len(val) > 20:
        return "Bearer [REDACTED]"
    return val


def sanitize_graph_body(obj: Any) -> Any:
    """Recursively remove or mask sensitive fields from a JSON-like structure.

    Args:
        obj: Parsed JSON (dict, list, scalar, or ``None``).

    Returns:
        Structure of the same shape safe to serialize to operator logs.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _is_sensitive_key(str(k)):
                out[str(k)] = "[REDACTED]"
            else:
                out[str(k)] = sanitize_graph_body(v)
        return out
    if isinstance(obj, list):
        return [sanitize_graph_body(item) for item in obj]
    return _sanitize_scalar(obj)


def _try_read_response_body(response: Any) -> Any:
    """Best-effort parse of an HTTP response body for error context.

    Args:
        response: Object optionally exposing ``json()`` or ``text``.

    Returns:
        Dict/list body, short string, or ``None`` if unreadable.
    """
    if response is None:
        return None
    try:
        if hasattr(response, "json"):
            raw = response.json()
            body = raw() if callable(raw) else raw
            if isinstance(body, (dict, list)):
                return body
            if body is not None:
                return str(body)
    except Exception:  # noqa: BLE001
        pass
    try:
        text_fn = getattr(response, "text", None)
        if callable(text_fn):
            t = text_fn()
            if t:
                return _sanitize_scalar(str(t))
    except Exception:  # noqa: BLE001
        pass
    return None


def _context_from_http_like_response(response: Any, base: dict[str, Any]) -> dict[str, Any]:
    """Merge HTTP status, correlation headers, and sanitized body into ``base``.

    Args:
        response: Object with ``status_code``, ``headers``, and parseable body.
        base: Initial context dict (e.g. operation name and exception type).

    Returns:
        Extended context dict suitable for JSON logging.
    """
    ctx = dict(base)
    status = getattr(response, "status_code", None)
    if status is not None:
        ctx["http_status"] = int(status)
    headers = getattr(response, "headers", None)
    rid = _header_get(headers, "request-id", "x-ms-request-id")
    if rid:
        ctx["request_id"] = rid
    crid = _header_get(headers, "client-request-id")
    if crid:
        ctx["client_request_id"] = crid
    raw_body = _try_read_response_body(response)
    if raw_body is not None:
        if isinstance(raw_body, (dict, list)):
            ctx["graph_body"] = sanitize_graph_body(raw_body)
        else:
            ctx["graph_body"] = str(raw_body)
    return ctx


def graph_failure_context(exc: BaseException, operation: str) -> dict[str, Any]:
    """Build a JSON-serializable dict describing a failure for file logging only.

    Args:
        exc: Any exception raised during Graph or credential operations.
        operation: Short label for the failing step (e.g. ``chapter_guests``).

    Returns:
        Dict with ``operation``, ``error_type``, ``message``, and when available
        ``http_status``, ``request_id``, ``client_request_id``, and ``graph_body``
        (sanitized). Never includes raw tokens or secrets.
    """
    ctx: dict[str, Any] = {
        "operation": operation,
        "error_type": type(exc).__name__,
        "message": str(exc) or type(exc).__name__,
    }

    if _HttpResponseError is not None and isinstance(exc, _HttpResponseError):
        if exc.response is not None:
            return _context_from_http_like_response(exc.response, ctx)

    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) is not None:
        return _context_from_http_like_response(response, ctx)

    msg = ctx.get("message", "")
    if isinstance(msg, str) and msg.lower().startswith("bearer ") and len(msg) > 24:
        ctx["message"] = "Bearer [REDACTED]"

    return ctx
