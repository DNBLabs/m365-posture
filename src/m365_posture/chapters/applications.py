"""Application registrations chapter: counts directory application objects."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def run_applications_chapter(fetch_applications: Callable[[], list[dict]]) -> ChapterResult:
    """Count application registration objects from a merged Graph list.

    Args:
        fetch_applications: Callable returning all ``/applications`` pages merged.

    Returns:
        :class:`ChapterResult` with ``application_count`` and an INFO finding.
    """
    applications = fetch_applications()
    application_count = len(applications)

    finding = Finding(
        severity="INFO",
        code="applications.count",
        message=f"Found {application_count} application registration(s) in sample.",
        evidence={"application_count": application_count},
    )

    return ChapterResult(
        chapter_id="applications",
        status="OK",
        data={"application_count": application_count},
        findings=[finding],
        error_summary=None,
    )
