"""Tests for report aggregation."""

from m365_posture.aggregate import build_report
from m365_posture.chapters.base import ChapterResult, Finding


def test_build_report_ok_and_degraded_counts_and_ordered_chapters() -> None:
    results = [
        ChapterResult(
            chapter_id="z_last",
            status="OK",
            data={"n": 1},
            findings=[],
            error_summary=None,
        ),
        ChapterResult(
            chapter_id="a_first",
            status="OK",
            data={},
            findings=[],
            error_summary=None,
        ),
        ChapterResult(
            chapter_id="m_mid",
            status="DEGRADED",
            data={},
            findings=[Finding(severity="WARN", code="c", message="m", evidence=None)],
            error_summary=None,
        ),
    ]
    report = build_report(
        results,
        tenant_id="tenant-test",
        generated_at="2024-06-15T10:00:00+00:00",
    )

    assert report["schemaVersion"] == 1
    assert report["generatedAt"] == "2024-06-15T10:00:00+00:00"
    assert report["tenantId"] == "tenant-test"
    assert report["summary"] == {"ok": 2, "degraded": 1}
    assert list(report["chapters"].keys()) == ["a_first", "m_mid", "z_last"]

    assert report["chapters"]["a_first"]["status"] == "OK"
    assert report["chapters"]["m_mid"]["status"] == "DEGRADED"
    assert len(report["chapters"]["m_mid"]["findings"]) == 1
    assert report["chapters"]["m_mid"]["findings"][0]["code"] == "c"
