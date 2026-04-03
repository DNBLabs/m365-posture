"""Guests chapter: enumerate guest-type directory users (read-only)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def _is_guest_user(user: dict) -> bool:
    """True if Graph marks the object as a guest or UPN matches common B2B guest shape."""
    if user.get("userType") == "Guest":
        return True
    upn = user.get("userPrincipalName")
    if isinstance(upn, str) and "#EXT#" in upn:
        return True
    return False


def run_guests_chapter(fetch_users: Callable[[], list[dict]]) -> ChapterResult:
    """
    Count guest users from a pre-fetched user list.

    Production code can pass a callable that pages Graph; tests inject static data.
    """
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
