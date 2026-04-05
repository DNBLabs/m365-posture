"""Deep-copy and redact personally identifiable information from report JSON.

Implements deterministic masking for emails, UPNs, display names, GUID-valued keys,
and tenant-specific domains so artifacts can be shared without exposing production
identifiers. GUIDs are replaced with stable short tokens derived from SHA-256 so
row-to-row correlation remains possible in redacted output.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_TEXT_REDACT_KEYS = frozenset(
    {
        "displayname",
        "userprincipalname",
        "mail",
        "email",
        "mailnickname",
        "othermails",
        "onpremisesuserprincipalname",
    }
)

_GUID_VALUE_KEYS = frozenset(
    {
        "id",
        "objectid",
        "tenantid",
        "applicationid",
        "appid",
        "serviceprincipalid",
        "deviceid",
        "groupid",
        "userid",
        "roleid",
        "assignmentid",
        "directoryobjectid",
        "parentid",
        "ownerid",
        "resourceid",
        "registeredownerid",
        "registeredusersid",
        "manageddeviceid",
    }
)


def _norm_key(key: str) -> str:
    """Normalize a dict key for case- and separator-insensitive lookups.

    Args:
        key: Original key string.

    Returns:
        Lowercase string with underscores removed.
    """
    return key.replace("_", "").lower()


def _is_email_like_key(key: str) -> bool:
    """Return True if a JSON key name suggests an email, UPN, or proxy address field.

    Graph returns varied property names; this uses heuristics beyond a fixed allowlist.

    Args:
        key: Object key from the report tree.

    Returns:
        ``True`` if values under this key should be fully redacted when strings.
    """
    nk = _norm_key(key)
    if nk in _TEXT_REDACT_KEYS:
        return True
    if nk == "proxyaddresses":
        return True
    if "emailaddress" in nk or nk.endswith("smtpaddress"):
        return True
    if "userprincipalname" in nk or nk.endswith("userprincipalname"):
        return True
    if nk.endswith("principalname") and "user" in nk:
        return True
    if nk.endswith("mail") and nk not in {"ismailboxenabled", "hasmailbox"}:
        return True
    return False


def _should_redact_plain_string(key: str) -> bool:
    """Return True if string values for ``key`` must be replaced with a placeholder.

    Args:
        key: JSON object key.

    Returns:
        ``True`` when the value should become ``[REDACTED]``.
    """
    return _is_email_like_key(key)


def _is_guid_value_key(key: str) -> bool:
    """Return True when the key identifies a GUID primary key field.

    Args:
        key: JSON object key.

    Returns:
        ``True`` if the value looks like a Graph object id and should be tokenized.
    """
    return _norm_key(key) in _GUID_VALUE_KEYS


def _optional_domain_scrub(text: str) -> str:
    """Mask ``@domain`` segments and ``*.onmicrosoft.com`` tenant DNS names.

    Args:
        text: Arbitrary string that may contain email or domain fragments.

    Returns:
        String with domains replaced by ``[REDACTED-DOMAIN]`` placeholders.
    """
    out = re.sub(r"@[^@\s]+", "[REDACTED-DOMAIN]", text)
    return re.sub(
        r"\b[\w.-]+\.onmicrosoft\.com\b",
        "[REDACTED-DOMAIN]",
        out,
        flags=re.IGNORECASE,
    )


def _stable_guid_token(guid: str) -> str:
    """Map a GUID string to a short stable token without revealing the raw GUID.

    Uses SHA-256 so the same input always yields the same token (useful for diffing
    redacted reports) while the original id cannot be recovered from the token alone.

    Args:
        guid: Canonical GUID string.

    Returns:
        Placeholder string ``[GUID-<8 hex chars>]``.
    """
    digest = hashlib.sha256(guid.strip().lower().encode("utf-8")).hexdigest()[:8]
    return f"[GUID-{digest}]"


def _redact_scalar(key: str, value: Any) -> Any:
    """Apply redaction rules to a single non-container value.

    Args:
        key: Parent object key for context-sensitive rules.
        value: Scalar value (typically str).

    Returns:
        Redacted value or the original value if no rule applies.
    """
    if not isinstance(value, str):
        return value
    if _is_guid_value_key(key) and _UUID_RE.match(value):
        return _stable_guid_token(value)
    if _should_redact_plain_string(key):
        return "[REDACTED]"
    if "@" in value or ".onmicrosoft." in value.lower():
        return _optional_domain_scrub(value)
    return value


def _redact_list(parent_key: str, items: list[Any]) -> list[Any]:
    """Redact each element of a list, using ``parent_key`` for string heuristics.

    Args:
        parent_key: Key whose value is this list (for email-like list fields).
        items: List elements (dicts, lists, or scalars).

    Returns:
        New list with redacted contents.
    """
    out: list[Any] = []
    for item in items:
        if isinstance(item, dict):
            out.append(_redact_walk(item))
        elif isinstance(item, list):
            out.append(_redact_list(parent_key, item))
        elif isinstance(item, str) and _is_email_like_key(parent_key):
            out.append("[REDACTED]")
        else:
            out.append(item)
    return out


def _redact_walk(obj: Any) -> Any:
    """Recursively redact dicts and lists in place logic (returns new structures).

    Args:
        obj: Any JSON-serializable subtree.

    Returns:
        Redacted copy of ``obj``.
    """
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                out[k] = _redact_walk(v)
            elif isinstance(v, list):
                out[k] = _redact_list(k, v)
            else:
                out[k] = _redact_scalar(k, v)
        return out
    if isinstance(obj, list):
        return [_redact_walk(item) for item in obj]
    return obj


def redact_report(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied report dict with PII and raw GUIDs redacted.

    Args:
        data: Top-level report object (typically from :func:`m365_posture.aggregate.build_report`).

    Returns:
        New dict safe for external sharing; original ``data`` is unchanged.
    """
    return _redact_walk(copy.deepcopy(data))
