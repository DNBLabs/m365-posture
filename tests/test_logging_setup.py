"""Tests for :func:`m365_posture.logging_setup.configure_logging`."""

import logging
from pathlib import Path

from m365_posture.logging_setup import configure_logging


def test_configure_logging_writes_to_file(tmp_path: Path) -> None:
    """Verify log records reach the configured file under the m365_posture logger.

    Args:
        tmp_path: Pytest temporary directory for an isolated log file.

    Returns:
        None.
    """
    log_path = tmp_path / "run.log"
    configure_logging(log_path)

    logging.getLogger("m365_posture").info("hello-test")

    text = log_path.read_text(encoding="utf-8")
    assert "hello-test" in text
