"""File-only logging setup for ``m365_posture``.

Handlers are attached to the dedicated logger named ``m365_posture`` (not the
root logger). Call ``logging.getLogger("m365_posture")`` or use a child logger
under that name so records reach the configured file.

**Do not add a StreamHandler here.** stdout/stderr can leak tokens if future
code logs sensitive payloads; the CLI will print user-facing summaries
separately (see ``cli.py``). This module configures **only** a
:class:`logging.FileHandler` at DEBUG level.
"""

from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_NAME = "m365_posture"
_FMT = "%(levelname)s %(name)s %(message)s"


def configure_logging(log_file: Path) -> None:
    """Attach a single DEBUG FileHandler on logger ``m365_posture``.

    Replaces any existing handlers on that logger so repeated setup in tests
    or reloads does not duplicate lines.
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
