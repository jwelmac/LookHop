"""Windows: 'Start with Windows' via the per-user Run registry key."""
from __future__ import annotations

import subprocess
import sys
import winreg
from pathlib import Path

from lookhop.config import APP_NAME, FROZEN, self_command

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command() -> str:
    cmd = self_command()
    if not FROZEN:  # from source: use pythonw so no console window appears
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if pythonw.exists():
            cmd[0] = str(pythonw)
    return subprocess.list2cmdline(cmd)


def autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
