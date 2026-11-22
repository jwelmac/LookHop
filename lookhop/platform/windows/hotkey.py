"""System-wide hotkey via Win32 RegisterHotKey (no keyboard hook needed)."""
from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import wintypes

log = logging.getLogger(__name__)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

MODIFIERS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
NAMED_KEYS = {"space": 0x20, "pause": 0x13, "scrolllock": 0x91, "home": 0x24,
              "end": 0x23, "insert": 0x2D, "pageup": 0x21, "pagedown": 0x22}
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 1


def parse_hotkey(spec: str) -> tuple[int, int]:
    mods, vk = 0, None
    for part in (p.strip().lower() for p in spec.split("+") if p.strip()):
        if part in MODIFIERS:
            mods |= MODIFIERS[part]
        elif len(part) == 1 and part.isalnum():
            vk = ord(part.upper())
        elif part.startswith("f") and part[1:].isdigit() and 1 <= int(part[1:]) <= 24:
            vk = 0x6F + int(part[1:])
        elif part in NAMED_KEYS:
            vk = NAMED_KEYS[part]
        else:
            raise ValueError(f"Unknown key {part!r} in hotkey {spec!r}")
    if vk is None or mods == 0:
        raise ValueError(f"Hotkey {spec!r} needs at least one modifier and one key")
    return mods | MOD_NOREPEAT, vk


class GlobalHotkey(threading.Thread):
    def __init__(self, spec: str, callback):
        super().__init__(daemon=True, name="hotkey")
        self.spec = spec
        self.mods, self.vk = parse_hotkey(spec)
        self.callback = callback
        self.ok = False
        self.ready = threading.Event()
        self._tid: int | None = None

    def run(self) -> None:
        self._tid = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, HOTKEY_ID, self.mods, self.vk):
            log.error("Could not register hotkey %s (error %d) - already used by another app?",
                      self.spec, ctypes.get_last_error())
            self.ready.set()
            return
        self.ok = True
        self.ready.set()
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    try:
                        self.callback()
                    except Exception:
                        log.exception("Hotkey callback failed")
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self) -> None:
        if self._tid is not None:
            user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
