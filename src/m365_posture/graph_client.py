"""Microsoft Graph HTTP helpers: OData page traversal and transient-error retries.

Implements bounded retries for Graph throttling (HTTP 429) and selected server
errors, honoring ``Retry-After`` when present. Non-retryable client errors fail
fast because repeating the request would not succeed without permission or input changes.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable

_TRANSIENT_STATUSES = frozenset({429, 503, 504})


def sleep_with_backoff(attempt: int, retry_after_sec: float | None = None) -> None:
    """Sleep before retrying a transient Graph failure using capped exponential backoff.

    Args:
        attempt: Zero-based retry attempt (used as exponent for ``2**attempt``).
        retry_after_sec: Optional ``Retry-After`` value from the response in seconds.

    Returns:
        None.
    """
    base = 0.5 * (2**attempt)
    backoff = min(base, 60.0) + random.uniform(0.0, 0.25)
    if retry_after_sec is not None:
        sleep_sec = max(backoff, float(retry_after_sec))
    else:
        sleep_sec = backoff
    time.sleep(sleep_sec)


def _parse_retry_after(headers: Any) -> float | None:
    """Parse a numeric ``Retry-After`` header from a response-like mapping.

    Args:
        headers: Object with ``.get`` (e.g. HTTP headers), or ``None``.

    Returns:
        Seconds to wait, or ``None`` if the header is missing or not numeric.
    """
    if headers is None or not hasattr(headers, "get"):
        return None
    raw = headers.get("Retry-After")
    if raw is None:
        raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def get_all_odata_pages(fetch_page: Callable[[str | None], dict]) -> list[Any]:
    """Merge all ``value`` entries across OData pages following ``@odata.nextLink``.

    Args:
        fetch_page: Callable taking ``None`` for the first URL, then each ``nextLink``
            string until the collection ends.

    Returns:
        Flattened list of items from every page's ``value`` array (may be mixed types).
    """
    merged: list[Any] = []
    next_url: str | None = None
    while True:
        page = fetch_page(next_url)
        values = page.get("value")
        if values is not None:
            merged.extend(values)
        next_link = page.get("@odata.nextLink") or page.get("odata.nextLink")
        if not next_link:
            break
        next_url = str(next_link)
    return merged


def execute_graph_get(
    url: str,
    get_with_response: Callable[[str], Any],
    *,
    max_attempts: int = 8,
) -> dict[str, Any]:
    """Perform a GET with retries on transient status codes.

    Args:
        url: Full Microsoft Graph URL.
        get_with_response: Function returning a response object with ``status_code``,
            ``headers``, and ``json()`` (or callable returning JSON).
        max_attempts: Maximum GET attempts including retries after backoff.

    Returns:
        Parsed JSON object (typically a dict) for a successful (2xx) response.

    Raises:
        RuntimeError: On non-retryable HTTP errors or when ``max_attempts`` is exceeded.
    """
    attempt = 0
    while attempt < max_attempts:
        response = get_with_response(url)
        code = int(getattr(response, "status_code", 0) or 0)
        if code in _TRANSIENT_STATUSES:
            ra = _parse_retry_after(getattr(response, "headers", None))
            sleep_with_backoff(attempt, ra)
            attempt += 1
            continue
        if 200 <= code < 300:
            raw = response.json()
            return raw() if callable(raw) else raw
        raise RuntimeError(f"Graph GET failed for {url!r} with HTTP {code}")

    raise RuntimeError(f"Graph GET exceeded max_attempts={max_attempts} for {url!r}")
