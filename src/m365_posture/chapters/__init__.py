"""Re-export chapter runner functions and shared result types for the CLI."""

from m365_posture.chapters.base import ChapterResult, Finding, chapter_result_to_dict
from m365_posture.chapters.guests import run_guests_chapter
from m365_posture.chapters.applications import run_applications_chapter
from m365_posture.chapters.devices import run_devices_chapter
from m365_posture.chapters.privileged import run_privileged_chapter
from m365_posture.chapters.signin_risk import run_signin_risk_chapter

__all__ = [
    "ChapterResult",
    "Finding",
    "chapter_result_to_dict",
    "run_applications_chapter",
    "run_devices_chapter",
    "run_guests_chapter",
    "run_privileged_chapter",
    "run_signin_risk_chapter",
]
