"""Unit tests for :func:`m365_posture.chapters.run_privileged_chapter` (no network)."""

import json
from pathlib import Path

from m365_posture.chapters import run_privileged_chapter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph" / "privileged_assignments.json"


def test_run_privileged_chapter_counts_assignments_from_fixture() -> None:
    """Assignment count and preview match the static role assignment fixture.

    Returns:
        None.
    """
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assignments = payload["value"]

    result = run_privileged_chapter(lambda: assignments)

    assert result.chapter_id == "privileged"
    assert result.status == "OK"
    assert result.error_summary is None
    assert result.data["assignment_count"] == 3
    assert result.data["preview_truncated"] is False
    assert len(result.data["assignments_preview"]) == 3

    infos = [f for f in result.findings if f.code == "privileged.assignment_count"]
    assert len(infos) == 1
    f0 = infos[0]
    assert f0.severity == "INFO"
    assert f0.evidence == {
        "assignment_count": 3,
        "preview_limit": 20,
        "preview_truncated": False,
    }
