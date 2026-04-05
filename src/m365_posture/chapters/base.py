"""Shared types for posture report chapters.

``Finding`` + ``ChapterResult`` are the contract between collectors and ``aggregate.build_report``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Finding:
    severity: Literal["INFO", "WARN"]
    code: str
    message: str
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class ChapterResult:
    chapter_id: str
    status: Literal["OK", "DEGRADED"]
    data: dict[str, Any]
    findings: list[Finding]
    error_summary: str | None = None


def chapter_result_to_dict(result: ChapterResult) -> dict[str, Any]:
    """Serialize a chapter result to a JSON-friendly dict (nested dataclasses become dicts)."""
    return asdict(result)
