"""Privileged access chapter: snapshot of directory role assignments (read-only)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding

_PREVIEW_LIMIT = 20


def _preview_row(assignment: dict) -> dict:
    """Extract a small stable subset of fields from one role assignment row.

    Args:
        assignment: Raw Graph ``roleAssignment``-like object.

    Returns:
        Dict with id, principal, role definition, and scope identifiers only.
    """
    return {
        "id": assignment.get("id"),
        "principalId": assignment.get("principalId"),
        "roleDefinitionId": assignment.get("roleDefinitionId"),
        "directoryScopeId": assignment.get("directoryScopeId"),
    }


def run_privileged_chapter(
    fetch_directory_role_assignments: Callable[[], list[dict]],
) -> ChapterResult:
    """Summarize directory role assignments from a merged list.

    Args:
        fetch_directory_role_assignments: Callable returning all assignment pages
            combined as a list of dicts.

    Returns:
        :class:`ChapterResult` with total count and a bounded preview list.
    """
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
