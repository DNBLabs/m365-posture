"""Managed devices chapter: Intune device summary by compliance and OS."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def _count_field(items: list[dict], key: str) -> dict[str, int]:
    """Build frequency counts for a string field across device rows.

    Args:
        items: List of managed device dicts.
        key: Property name (e.g. ``complianceState``).

    Returns:
        Sorted map of label to count; missing values are labeled ``unknown``.
    """
    counts: dict[str, int] = {}
    for row in items:
        raw = row.get(key)
        label = raw if isinstance(raw, str) and raw.strip() else "unknown"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def run_devices_chapter(fetch_managed_devices: Callable[[], list[dict]]) -> ChapterResult:
    """Summarize managed devices from a merged list.

    Args:
        fetch_managed_devices: Callable returning all ``managedDevices`` pages merged.

    Returns:
        :class:`ChapterResult` with totals and per-field breakdowns.
    """
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
