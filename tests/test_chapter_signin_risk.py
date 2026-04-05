"""Unit tests for :func:`m365_posture.chapters.run_signin_risk_chapter` (no network)."""

from m365_posture.chapters import run_signin_risk_chapter


def test_run_signin_risk_chapter_empty_list_ok() -> None:
    """Zero sign-ins yields OK status and zero count in findings.

    Returns:
        None.
    """
    result = run_signin_risk_chapter(lambda: [])

    assert result.chapter_id == "signin_risk"
    assert result.status == "OK"
    assert result.error_summary is None
    assert result.data["sign_in_record_count"] == 0

    assert len(result.findings) == 1
    f0 = result.findings[0]
    assert f0.severity == "INFO"
    assert f0.code == "signin_risk.count"
    assert f0.evidence == {"sign_in_record_count": 0}


def test_run_signin_risk_chapter_fetch_raises_degraded() -> None:
    """Generic exceptions from the fetch callable produce DEGRADED without raising.

    Returns:
        None.
    """

    def boom() -> list[dict]:
        """Simulate Graph transport failure."""
        raise RuntimeError("network")

    result = run_signin_risk_chapter(boom)

    assert result.chapter_id == "signin_risk"
    assert result.status == "DEGRADED"
    assert result.data == {}
    assert result.findings == []
    assert result.error_summary == "Sign-in activity could not be retrieved."


def test_run_signin_risk_chapter_permission_error_degraded() -> None:
    """PermissionError maps to a specific audit-permissions error summary.

    Returns:
        None.
    """

    def denied() -> list[dict]:
        """Simulate missing directory/audit permissions."""
        raise PermissionError("insufficient privileges")

    result = run_signin_risk_chapter(denied)

    assert result.status == "DEGRADED"
    assert result.findings == []
    assert result.error_summary == (
        "Sign-in activity could not be read (directory or audit permissions may be missing)."
    )
