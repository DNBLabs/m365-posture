"""Minimal Microsoft Graph HTTP GET client using the Python standard library.

Uses ``urllib`` instead of adding a third-party HTTP dependency; responses are
adapted to the shape expected by :func:`m365_posture.graph_client.execute_graph_get`.
Bearer tokens are obtained from an Azure ``TokenCredential`` for the Graph
``https://graph.microsoft.com/.default`` scope.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from azure.core.credentials import TokenCredential


class GraphHttpResponse:
    """Adapter exposing ``status_code``, ``headers``, and ``json()`` for Graph GET results."""

    __slots__ = ("status_code", "headers", "_raw_body")

    def __init__(self, status_code: int, headers: dict[str, str], body: bytes) -> None:
        """Store raw response parts for lazy JSON parsing.

        Args:
            status_code: HTTP status integer.
            headers: Lowercased header names from the underlying response.
            body: Raw response body bytes.
        """
        self.status_code = status_code
        self.headers = headers
        self._raw_body = body

    def json(self) -> Any:
        """Decode the body as JSON, or return an empty dict on decode failure.

        Returns:
            Parsed JSON (usually dict), or ``{}`` if body is empty or invalid JSON.
        """
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
    """Create a closure that performs authenticated GET requests to Graph URLs.

    Args:
        credential: Azure credential capable of issuing tokens for Graph.

    Returns:
        A single-argument function ``get(url: str) -> GraphHttpResponse`` that adds
        a Bearer token and returns a parsed response wrapper.
    """

    scope = "https://graph.microsoft.com/.default"

    def get(url: str) -> GraphHttpResponse:
        """Execute GET ``url`` with a fresh Bearer token.

        Args:
            url: Full Microsoft Graph request URL.

        Returns:
            :class:`GraphHttpResponse` with status, headers, and body.

        Raises:
            URLError: On network-level failures from ``urlopen``.
        """
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
