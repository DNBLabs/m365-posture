"""HTML report rendering from `build_report` envelopes."""

from __future__ import annotations

from m365_posture.aggregate import build_report
from m365_posture.chapters.base import ChapterResult, Finding
from m365_posture.render import render_html


def test_render_html_includes_chapter_id_and_severity_strings() -> None:
    chapters = [
        ChapterResult(
            chapter_id="guests",
            status="OK",
            data={},
            findings=[
                Finding(
                    severity="INFO",
                    code="G-1",
                    message="Example info finding",
                    evidence=None,
                )
            ],
            error_summary=None,
        ),
    ]
    report = build_report(
        chapters,
        tenant_id="tenant-test",
        generated_at="2026-04-03T12:00:00+00:00",
    )
    html = render_html(report)
    assert "guests" in html
    assert "INFO" in html
    assert "Schema version" in html
    assert "2026-04-03T12:00:00+00:00" in html
    assert "1 OK" in html
