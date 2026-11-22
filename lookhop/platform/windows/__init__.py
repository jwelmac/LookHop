"""Windows backend (complete). Pure Win32 via ctypes - no extra dependencies."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path

from lookhop.platform.windows.autostart import autostart_enabled, set_autostart
from lookhop.platform.windows.display import (get_cursor, last_input_tick, list_screens,
                                              make_dpi_aware, message_box, mouse_button_down,
                                              set_cursor)
from lookhop.platform.windows.focus import focus_screen
from lookhop.platform.windows.hotkey import GlobalHotkey, parse_hotkey

NAME = "Windows"
SUPPORTED = True
ERROR_ALREADY_EXISTS = 183
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateMutexW.restype = ctypes.c_void_p


def acquire_single_instance(app_name: str):
    """Returns a handle to keep for the process lifetime, or None if already running."""
    handle = _kernel32.CreateMutexW(None, False, f"Local\\{app_name}-single-instance")
    if not handle or ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        return None
    return handle


def open_file(path: Path) -> None:
    """Open a text/log file for the user."""
    try:
        os.startfile(str(path))  # default app for .json / .log
    except OSError:
        import subprocess
        subprocess.Popen(["notepad.exe", str(path)])


__all__ = ["NAME", "SUPPORTED", "acquire_single_instance", "autostart_enabled", "focus_screen",
           "get_cursor", "GlobalHotkey", "last_input_tick", "list_screens", "make_dpi_aware",
           "message_box", "mouse_button_down", "open_file", "parse_hotkey", "set_autostart",
           "set_cursor"]
