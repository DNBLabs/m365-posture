"""Devices chapter: managed device summary from Intune / Graph (read-only)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def _count_field(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in items:
        raw = row.get(key)
        label = raw if isinstance(raw, str) and raw.strip() else "unknown"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def run_devices_chapter(fetch_managed_devices: Callable[[], list[dict]]) -> ChapterResult:
    """Roll up managed devices by compliance and OS; input list is fully paged by the caller."""
    devices = fetch_managed_devices()
    total = len(devices)
    by_compliance = _count_field(devices, "complianceState")
    by_operating_system = _count_field(devices, "operatingSystem")

    finding = Finding(
        severity="INFO",
        code="devices.summary",
        message=f"Sampled {total} managed device(s); compliance and OS breakdown in evidence.",
        evidence={
            "managed_device_count": total,
            "by_compliance_state": by_compliance,
            "by_operating_system": by_operating_system,
        },
    )

    return ChapterResult(
        chapter_id="devices",
        status="OK",
        data={
            "managed_device_count": total,
            "by_compliance_state": by_compliance,
            "by_operating_system": by_operating_system,
        },
        findings=[finding],
        error_summary=None,
    )
