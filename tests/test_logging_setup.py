import logging
from pathlib import Path

from m365_posture.logging_setup import configure_logging


def test_configure_logging_writes_to_file(tmp_path: Path) -> None:
    log_path = tmp_path / "run.log"
    configure_logging(log_path)

    logging.getLogger("m365_posture").info("hello-test")

    text = log_path.read_text(encoding="utf-8")
    assert "hello-test" in text
