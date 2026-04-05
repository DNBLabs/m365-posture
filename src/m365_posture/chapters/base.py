"""Dataclasses describing posture chapter outputs and serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Finding:
    """A single human-readable insight produced by a chapter.

    Attributes:
        severity: ``INFO`` for informational counts, ``WARN`` for attention items.
        code: Stable machine-readable code (e.g. ``guest.count``).
        message: Short sentence for reports.
        evidence: Optional small dict with counts or samples (subject to redaction).
    """

    severity: Literal["INFO", "WARN"]
    code: str
    message: str
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class ChapterResult:
    """Outcome of one chapter run against Microsoft Graph or fixtures.

    Attributes:
        chapter_id: Internal id (``guests``, ``privileged``, etc.).
        status: ``OK`` if the chapter completed, ``DEGRADED`` on partial failure.
        data: Chapter-specific summary fields for JSON and HTML.
        findings: List of :class:`Finding` entries.
        error_summary: Short operator message when ``DEGRADED``, else ``None``.
    """

    chapter_id: str
    status: Literal["OK", "DEGRADED"]
    data: dict[str, Any]
    findings: list[Finding]
    error_summary: str | None = None


def chapter_result_to_dict(result: ChapterResult) -> dict[str, Any]:
    """Convert a chapter result to nested dicts suitable for JSON serialization.

    Args:
        result: Frozen dataclass instance.

    Returns:
        Dict with keys matching :class:`ChapterResult` fields.
    """
    return asdict(result)
