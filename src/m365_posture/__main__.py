"""Allow ``python -m m365_posture`` (e.g. Task Scheduler)."""

from m365_posture.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
