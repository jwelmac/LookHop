"""Bring the top window on a screen to the foreground - Alt+Tab, but per screen.

"Top window on that screen" = the first window, in Z-order, that Alt+Tab would
show and whose largest part is on that screen. That's the app you were last
using there.
"""
from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

from lookhop.platform.base import Screen
from lookhop.platform.windows.display import _MONITORINFOEXW

log = logging.getLogger(__name__)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi")

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
GA_ROOTOWNER = 3
DWMWA_CLOAKED = 14
MONITOR_DEFAULTTONEAREST = 2
INPUT_MOUSE = 0
# Desktop, taskbars and shell overlays are never "the app on that screen".
SKIP_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
                "Windows.UI.Core.CoreWindow", "XamlExplorerHostIslandWindow"}

HWND = wintypes.HWND
user32.GetForegroundWindow.restype = HWND
user32.GetAncestor.restype = HWND
user32.GetAncestor.argtypes = [HWND, wintypes.UINT]
user32.GetLastActivePopup.restype = HWND
user32.GetLastActivePopup.argtypes = [HWND]
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.GetWindowLongPtrW.argtypes = [HWND, ctypes.c_int]
user32.MonitorFromWindow.restype = wintypes.HMONITOR
user32.MonitorFromWindow.argtypes = [HWND, wintypes.DWORD]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(wintypes.DWORD)]
user32.IsWindowVisible.argtypes = [HWND]
user32.IsIconic.argtypes = [HWND]
user32.GetWindowTextLengthW.argtypes = [HWND]
user32.GetClassNameW.argtypes = [HWND, wintypes.LPWSTR, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [HWND]
user32.BringWindowToTop.argtypes = [HWND]
dwmapi.DwmGetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

_EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, HWND, wintypes.LPARAM)


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT), ("hi", _HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _class_name(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _is_cloaked(hwnd) -> bool:
    """Hidden UWP frames and windows on other virtual desktops are 'cloaked'."""
    value = ctypes.c_int(0)
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(value), ctypes.sizeof(value))
    return value.value != 0


def _monitor_name(hwnd) -> str | None:
    hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    info = _MONITORINFOEXW()
    info.cbSize = ctypes.sizeof(info)
    if not hmon or not user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
        return None
    return info.szDevice


def _is_alt_tab_window(hwnd) -> bool:
    if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
        return False
    if user32.GetAncestor(hwnd, GA_ROOTOWNER) != hwnd:  # owned popups ride with their owner
        return False
    ex = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    if ex & (WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE):
        return False
    if user32.GetWindowTextLengthW(hwnd) == 0:
        return False
    if _class_name(hwnd) in SKIP_CLASSES:
        return False
    return not _is_cloaked(hwnd)


def top_window_on(screen: Screen):
    found = []

    def cb(hwnd, _lparam):
        if hwnd and _is_alt_tab_window(hwnd) and _monitor_name(hwnd) == screen.name:
            found.append(hwnd)
            return False  # stop: EnumWindows walks top-down in Z-order
        return True

    user32.EnumWindows(_EnumWindowsProc(cb), 0)
    return found[0] if found else None


def _send_null_input() -> None:
    """A zero-length mouse event. Windows only lets the process that received
    the latest input change the foreground window; this makes that us, without
    pressing any key (the same trick PowerToys uses)."""
    inp = _INPUT(type=INPUT_MOUSE)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def _activate(hwnd) -> bool:
    popup = user32.GetLastActivePopup(hwnd)  # e.g. a Save dialog belonging to the window
    if popup and user32.IsWindowVisible(popup):
        hwnd = popup
    _send_null_input()
    user32.SetForegroundWindow(hwnd)
    if user32.GetForegroundWindow() == hwnd:
        return True

    # Fallback: share the current foreground thread's input state for a moment.
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    me = kernel32.GetCurrentThreadId()
    attached = bool(fg_tid and fg_tid != me and user32.AttachThreadInput(me, fg_tid, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(me, fg_tid, False)
    return user32.GetForegroundWindow() == hwnd


def focus_screen(screen: Screen) -> bool:
    """Activate the top window on `screen`, unless the active window is already there."""
    fg = user32.GetForegroundWindow()
    if fg and _monitor_name(fg) == screen.name and _is_alt_tab_window(fg):
        return False
    hwnd = top_window_on(screen)
    if hwnd is None:
        return False
    ok = _activate(hwnd)
    if not ok:
        log.debug("Could not activate window on %s", screen.name)
    return ok
