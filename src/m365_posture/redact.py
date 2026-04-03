"""Redact PII and tenant identifiers from report-shaped JSON (§3 defaults)."""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Keys whose string values are masked as [REDACTED] (emails, UPNs, display names, adjacent fields).
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
    return key.replace("_", "").lower()


def _is_email_like_key(key: str) -> bool:
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
    return _is_email_like_key(key)


def _is_guid_value_key(key: str) -> bool:
    return _norm_key(key) in _GUID_VALUE_KEYS


def _optional_domain_scrub(text: str) -> str:
    out = re.sub(r"@[^@\s]+", "[REDACTED-DOMAIN]", text)
    return re.sub(
        r"\b[\w.-]+\.onmicrosoft\.com\b",
        "[REDACTED-DOMAIN]",
        out,
        flags=re.IGNORECASE,
    )


def _stable_guid_token(guid: str) -> str:
    digest = hashlib.sha256(guid.strip().lower().encode("utf-8")).hexdigest()[:8]
    return f"[GUID-{digest}]"


def _redact_scalar(key: str, value: Any) -> Any:
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
    """Return a deep-redacted copy of ``data`` (dict/list tree)."""
    return _redact_walk(copy.deepcopy(data))
