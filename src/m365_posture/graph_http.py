"""Minimal Graph HTTP client using stdlib urllib plus Azure TokenCredential.

urllib keeps the dependency surface small for a CLI; timeouts and sizes are bounded in callers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from azure.core.credentials import TokenCredential


class GraphHttpResponse:
    """Response shape expected by :func:`m365_posture.graph_client.execute_graph_get`."""

    __slots__ = ("status_code", "headers", "_raw_body")

    def __init__(self, status_code: int, headers: dict[str, str], body: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self._raw_body = body

    def json(self) -> Any:
        if not self._raw_body:
            return {}
        try:
            text = self._raw_body.decode("utf-8")
        except UnicodeDecodeError:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


def authenticated_get_factory(credential: TokenCredential) -> Callable[[str], GraphHttpResponse]:
    """Return a GET function that injects a Graph Bearer token from the credential."""

    scope = "https://graph.microsoft.com/.default"

    def get(url: str) -> GraphHttpResponse:
        access = credential.get_token(scope)
        token = access.token
        req = Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urlopen(req, timeout=120) as resp:
                body = resp.read()
                code = getattr(resp, "status", resp.getcode())
                hdrs = {k: v for k, v in resp.headers.items()}
        except HTTPError as e:
            body = e.read() if e.fp else b""
            code = e.code
            hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
        except URLError:
            raise
        return GraphHttpResponse(int(code), hdrs, body)

    return get
