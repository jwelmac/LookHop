"""macOS: 'Start at login' via a per-user LaunchAgent."""
from __future__ import annotations

import plistlib
from pathlib import Path

from lookhop.config import FROZEN, SOURCE_ROOT, self_command

LABEL = "io.github.shubhendam.lookhop"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def autostart_enabled() -> bool:
    return PLIST.exists()


def set_autostart(enabled: bool) -> None:
    if not enabled:
        PLIST.unlink(missing_ok=True)
        return
    job = {"Label": LABEL, "ProgramArguments": self_command(), "RunAtLoad": True,
           "ProcessType": "Interactive"}
    if not FROZEN:  # from source: `python -m lookhop` must run from the repo
        job["WorkingDirectory"] = str(SOURCE_ROOT)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    with open(PLIST, "wb") as f:
        plistlib.dump(job, f)
