"""Privileged chapter: directory role assignments snapshot (read-only)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding

_PREVIEW_LIMIT = 20


def _preview_row(a: dict) -> dict:
    # Keep a bounded preview so HTML/JSON stays readable on tenants with many assignments.
    return {
        "id": a.get("id"),
        "principalId": a.get("principalId"),
        "roleDefinitionId": a.get("roleDefinitionId"),
        "directoryScopeId": a.get("directoryScopeId"),
    }


def run_privileged_chapter(
    fetch_directory_role_assignments: Callable[[], list[dict]],
) -> ChapterResult:
    """Summarize role assignments; ``fetch_directory_role_assignments`` is paged in production."""
    assignments = fetch_directory_role_assignments()
    assignment_count = len(assignments)
    preview = [_preview_row(a) for a in assignments[:_PREVIEW_LIMIT]]
    preview_truncated = assignment_count > _PREVIEW_LIMIT

    finding = Finding(
        severity="INFO",
        code="privileged.assignment_count",
        message=f"Found {assignment_count} directory role assignment(s).",
        evidence={
            "assignment_count": assignment_count,
            "preview_limit": _PREVIEW_LIMIT,
            "preview_truncated": preview_truncated,
        },
    )

    return ChapterResult(
        chapter_id="privileged",
        status="OK",
        data={
            "assignment_count": assignment_count,
            "assignments_preview": preview,
            "preview_truncated": preview_truncated,
            "preview_limit": _PREVIEW_LIMIT,
        },
        findings=[finding],
        error_summary=None,
    )
