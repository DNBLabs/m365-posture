"""Unit tests for guests chapter (no network)."""

import json
from pathlib import Path

from m365_posture.chapters import run_guests_chapter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph" / "guest_users_page.json"


def test_run_guests_chapter_counts_guests_from_fixture() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    users = payload["value"]

    result = run_guests_chapter(lambda: users)

    assert result.chapter_id == "guests"
    assert result.status == "OK"
    assert result.error_summary is None
    assert result.data["guest_user_count"] == 2
    assert result.data["total_sampled"] == 4

    assert len(result.findings) >= 1
    count_findings = [f for f in result.findings if f.code == "guest.count"]
    assert len(count_findings) == 1
    f0 = count_findings[0]
    assert f0.severity == "INFO"
    assert f0.evidence == {"guest_user_count": 2, "total_sampled": 4}
