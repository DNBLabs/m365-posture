"""Configure file-only logging for the ``m365_posture`` package logger.

Attaches a single DEBUG-level :class:`logging.FileHandler` to the logger named
``m365_posture`` and disables propagation to the root logger. Standard streams
are intentionally not used so accidental logging of response bodies cannot echo
tokens to the console; the CLI prints short user-facing status lines separately.
"""

from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_NAME = "m365_posture"
_FMT = "%(levelname)s %(name)s %(message)s"


def configure_logging(log_file: Path) -> None:
    """Attach one DEBUG file handler to the ``m365_posture`` logger.

    Args:
        log_file: Path to the log file (parent directories are created if needed).

    Returns:
        None. Replaces any existing handlers on the same logger to avoid duplicate
        log lines when tests or imports call this repeatedly.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger(_LOGGER_NAME)
    log.setLevel(logging.DEBUG)

    for h in list(log.handlers):
        log.removeHandler(h)
        h.close()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FMT))
    log.addHandler(fh)
    log.propagate = False
