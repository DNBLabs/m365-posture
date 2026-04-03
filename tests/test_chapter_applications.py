"""Unit tests for applications chapter (no network)."""

import json
from pathlib import Path

from m365_posture.chapters import run_applications_chapter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph" / "applications_page.json"


def test_run_applications_chapter_counts_from_fixture() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    apps = payload["value"]

    result = run_applications_chapter(lambda: apps)

    assert result.chapter_id == "applications"
    assert result.status == "OK"
    assert result.error_summary is None
    assert result.data["application_count"] == 4

    infos = [f for f in result.findings if f.code == "applications.count"]
    assert len(infos) == 1
    f0 = infos[0]
    assert f0.severity == "INFO"
    assert f0.evidence == {"application_count": 4}
