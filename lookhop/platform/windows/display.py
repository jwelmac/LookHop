"""Windows: DPI awareness, display layout, cursor, input state."""
from __future__ import annotations

import ctypes
from ctypes import wintypes

from lookhop.platform.base import Screen

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]

VK_LBUTTON, VK_RBUTTON, VK_MBUTTON = 0x01, 0x02, 0x04
MONITORINFOF_PRIMARY = 0x1


def make_dpi_aware() -> None:
    """Use physical pixels everywhere so coordinates match across mixed-DPI displays.
    Must run before any window (Tk, OpenCV, tray) is created."""
    try:
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
            return
    except AttributeError:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


class _MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


_MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
)


def list_screens() -> list[Screen]:
    screens: list[Screen] = []

    def _cb(hmon, _hdc, _rect, _data):
        info = _MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            r = info.rcMonitor
            screens.append(Screen(info.szDevice, r.left, r.top, r.right, r.bottom,
                                  bool(info.dwFlags & MONITORINFOF_PRIMARY)))
        return True

    user32.EnumDisplayMonitors(None, None, _MonitorEnumProc(_cb), 0)
    return screens


def get_cursor() -> tuple[int, int] | None:
    pt = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(pt)):  # fails on lock screen / UAC desktop
        return None
    return pt.x, pt.y


def set_cursor(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))


def mouse_button_down() -> bool:
    return any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in (VK_LBUTTON, VK_RBUTTON, VK_MBUTTON))


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def last_input_tick() -> int:
    """Tick count of the most recent keyboard/mouse input anywhere in the session."""
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    user32.GetLastInputInfo(ctypes.byref(info))
    return info.dwTime


def message_box(text: str, title: str, error: bool = False) -> None:
    user32.MessageBoxW(None, text, title, 0x10 if error else 0x40)
