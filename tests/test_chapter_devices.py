"""Unit tests for managed devices chapter (no network)."""

import json
from pathlib import Path

from m365_posture.chapters import run_devices_chapter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph" / "managed_devices.json"


def test_run_devices_chapter_summarizes_fixture() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    devices = payload["value"]

    result = run_devices_chapter(lambda: devices)

    assert result.chapter_id == "devices"
    assert result.status == "OK"
    assert result.error_summary is None
    assert result.data["managed_device_count"] == 4
    assert result.data["by_compliance_state"] == {
        "compliant": 2,
        "noncompliant": 1,
        "unknown": 1,
    }
    assert result.data["by_operating_system"] == {
        "Android": 1,
        "Windows": 2,
        "macOS": 1,
    }

    infos = [f for f in result.findings if f.code == "devices.summary"]
    assert len(infos) == 1
    f0 = infos[0]
    assert f0.severity == "INFO"
    assert f0.evidence == {
        "managed_device_count": 4,
        "by_compliance_state": {
            "compliant": 2,
            "noncompliant": 1,
            "unknown": 1,
        },
        "by_operating_system": {"Android": 1, "Windows": 2, "macOS": 1},
    }
