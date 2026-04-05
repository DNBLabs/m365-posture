"""Entry point for ``python -m m365_posture`` (e.g. Windows Task Scheduler)."""

from m365_posture.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
