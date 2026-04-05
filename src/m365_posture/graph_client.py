"""Graph HTTP helpers: OData pagination and transient-error retries."""

from __future__ import annotations

import random
import time
from typing import Any, Callable

# Transient statuses honored by execute_graph_get
_TRANSIENT_STATUSES = frozenset({429, 503, 504})


def sleep_with_backoff(attempt: int, retry_after_sec: float | None = None) -> None:
    """
    Capped exponential backoff with jitter. Base ~0.5s, multiply by 2**attempt,
    cap 60s, plus uniform jitter in [0, 0.25).

    If the server sent Retry-After (seconds), sleep for max(computed_backoff, retry_after_sec).
    """
    base = 0.5 * (2**attempt)
    backoff = min(base, 60.0) + random.uniform(0.0, 0.25)
    if retry_after_sec is not None:
        sleep_sec = max(backoff, float(retry_after_sec))
    else:
        sleep_sec = backoff
    time.sleep(sleep_sec)


def _parse_retry_after(headers: Any) -> float | None:
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
    """
    Follow @odata.nextLink / odata.nextLink until exhausted.

    The first page is requested with ``fetch_page(None)``; subsequent calls receive
    the next URL string from the prior response.
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
    """
    GET ``url`` with retries on 429 / 503 / 504 using :func:`sleep_with_backoff`
    and optional ``Retry-After`` header (numeric seconds).

    ``get_with_response`` must return an object with ``status_code``, ``headers``, and ``json()``.
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
        # Non-transient 4xx/5xx: retrying would not help without changing inputs or permissions.
        raise RuntimeError(f"Graph GET failed for {url!r} with HTTP {code}")

    raise RuntimeError(f"Graph GET exceeded max_attempts={max_attempts} for {url!r}")
