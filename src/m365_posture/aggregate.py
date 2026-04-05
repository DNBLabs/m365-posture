"""Merge per-chapter results into a single versioned JSON report envelope.

The output shape includes ``schemaVersion`` for contract tests; bumping the version
is a breaking change for golden-file comparisons.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from m365_posture.chapters.base import ChapterResult, chapter_result_to_dict


def build_report(
    chapter_results: list[ChapterResult],
    *,
    tenant_id: str,
    schema_version: int = 1,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Combine chapter results into one JSON-serializable report document.

    Args:
        chapter_results: Completed chapter runs (``OK`` or ``DEGRADED``).
        tenant_id: Tenant identifier to embed in the report (may be redacted later).
        schema_version: Report format version; increment when the envelope changes.
        generated_at: ISO-8601 timestamp; defaults to current UTC time if omitted.

    Returns:
        Dict with ``schemaVersion``, ``generatedAt``, ``tenantId``, ``summary``
        counts, and a ``chapters`` map keyed by chapter id.
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    ok = sum(1 for c in chapter_results if c.status == "OK")
    degraded = sum(1 for c in chapter_results if c.status == "DEGRADED")

    chapters: dict[str, Any] = {}
    for r in sorted(chapter_results, key=lambda c: c.chapter_id):
        chapters[r.chapter_id] = chapter_result_to_dict(r)

    return {
        "schemaVersion": schema_version,
        "generatedAt": generated_at,
        "tenantId": tenant_id,
        "summary": {"ok": ok, "degraded": degraded},
        "chapters": chapters,
    }
