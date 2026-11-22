"""Shared placeholder pieces for backends that aren't written yet.

A backend that isn't ready sets SUPPORTED = False; the app then shows a
friendly "not supported yet - contributions welcome" message and exits.
"""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

REPO_URL = "https://github.com/shubhendam/LookHop"


class NotPortedYet(NotImplementedError):
    def __init__(self, what: str, os_name: str):
        super().__init__(f"{what} is not implemented for {os_name} yet. "
                         f"See CONTRIBUTING.md ({REPO_URL}) - help wanted!")


def tk_message_box(text: str, title: str, error: bool = False) -> None:
    """Cross-platform message box (Tk ships with Python on every OS)."""
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    (messagebox.showerror if error else messagebox.showinfo)(title, text)
    root.destroy()


def open_file(path: Path) -> None:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])


class NoHotkey(threading.Thread):
    """Stand-in for GlobalHotkey: starts, reports failure, does nothing."""

    def __init__(self, spec: str, callback):
        super().__init__(daemon=True)
        self.ok = False
        self.ready = threading.Event()
        self.ready.set()

    def run(self) -> None:
        pass

    def stop(self) -> None:
        pass
