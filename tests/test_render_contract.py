"""Golden JSON contract for :func:`m365_posture.aggregate.build_report`.

Bump ``schemaVersion`` in ``m365_posture.aggregate.build_report`` and update
``tests/golden/report_v1.json`` intentionally when the report envelope or serialized
chapter shape changes.
"""

from __future__ import annotations

import json
from pathlib import Path

from m365_posture.aggregate import build_report
from m365_posture.chapters.base import ChapterResult, Finding

GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "report_v1.json"

_FIXED_GENERATED_AT = "2026-04-03T00:00:00+00:00"
_FIXED_TENANT = "tenant-golden-00000000-0000-0000-0000-000000000001"


def _normalize_report(obj: object) -> str:
    """Serialize ``obj`` with sorted keys for stable string comparison.

    Args:
        obj: JSON-serializable object (typically a report dict).

    Returns:
        Canonical JSON string without whitespace variance.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _fixed_chapters() -> list[ChapterResult]:
    """Build a deterministic list of chapter results matching the golden file.

    Returns:
        Fixed multi-chapter scenario for contract testing.
    """
    return [
        ChapterResult(
            chapter_id="applications",
            status="OK",
            data={"count": 0},
            findings=[],
            error_summary=None,
        ),
        ChapterResult(
            chapter_id="devices",
            status="DEGRADED",
            data={},
            findings=[Finding(severity="WARN", code="x", message="m", evidence=None)],
            error_summary="err",
        ),
        ChapterResult(
            chapter_id="guests",
            status="OK",
            data={},
            findings=[],
            error_summary=None,
        ),
    ]


def test_build_report_matches_golden_v1() -> None:
    """Current ``build_report`` output must match ``tests/golden/report_v1.json`` exactly.

    Returns:
        None.
    """
    report = build_report(
        _fixed_chapters(),
        tenant_id=_FIXED_TENANT,
        generated_at=_FIXED_GENERATED_AT,
    )
    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert _normalize_report(report) == _normalize_report(expected)
