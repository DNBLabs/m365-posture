"""Sign-in risk chapter: optional sign-in activity sample (read-only, graceful degradation)."""

from __future__ import annotations

from collections.abc import Callable

from m365_posture.chapters.base import ChapterResult, Finding


def run_signin_risk_chapter(fetch_sign_ins: Callable[[], list[dict]]) -> ChapterResult:
    """Summarize a sign-in sample; failures become DEGRADED without raising (optional chapter)."""
    try:
        sign_ins = fetch_sign_ins()
    except PermissionError:
        return ChapterResult(
            chapter_id="signin_risk",
            status="DEGRADED",
            data={},
            findings=[],
            error_summary=(
                "Sign-in activity could not be read (directory or audit permissions may be missing)."
            ),
        )
    except Exception:  # noqa: BLE001 — any transport/Graph error should downgrade this optional chapter
        return ChapterResult(
            chapter_id="signin_risk",
            status="DEGRADED",
            data={},
            findings=[],
            error_summary="Sign-in activity could not be retrieved.",
        )

    count = len(sign_ins)
    finding = Finding(
        severity="INFO",
        code="signin_risk.count",
        message=f"Collected {count} sign-in record(s) in sample.",
        evidence={"sign_in_record_count": count},
    )

    return ChapterResult(
        chapter_id="signin_risk",
        status="OK",
        data={"sign_in_record_count": count},
        findings=[finding],
        error_summary=None,
    )
