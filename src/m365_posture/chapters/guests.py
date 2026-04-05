"""Guests chapter: enumerate guest-type directory users (read-only)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def _is_guest_user(user: dict) -> bool:
    if user.get("userType") == "Guest":
        return True
    upn = user.get("userPrincipalName")
    # B2B guests often carry "#EXT#" in the UPN even when userType is absent in partial projections.
    if isinstance(upn, str) and "#EXT#" in upn:
        return True
    return False


def run_guests_chapter(fetch_users: Callable[[], list[dict]]) -> ChapterResult:
    """Count guests; ``fetch_users`` pages Graph in production and returns fixtures in tests."""
    users = fetch_users()
    total_sampled = len(users)
    guest_user_count = sum(1 for u in users if _is_guest_user(u))

    finding = Finding(
        severity="INFO",
        code="guest.count",
        message=f"Found {guest_user_count} guest user(s) in sample of {total_sampled}.",
        evidence={"guest_user_count": guest_user_count, "total_sampled": total_sampled},
    )

    return ChapterResult(
        chapter_id="guests",
        status="OK",
        data={"guest_user_count": guest_user_count, "total_sampled": total_sampled},
        findings=[finding],
        error_summary=None,
    )
