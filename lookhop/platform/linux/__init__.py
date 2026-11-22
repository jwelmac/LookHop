"""Linux backend - NOT IMPLEMENTED YET (help wanted!).

Everything else in LookHop (camera, face tracking, calibration, control panel,
tray) is cross-platform already. To port it, implement the functions below and
set SUPPORTED = True.

X11 (doable today, e.g. with python-xlib or ewmh):
  list_screens       RandR monitors (xrandr) - positions in the root window
  get_cursor         root.query_pointer()
  set_cursor         root.warp_pointer(x, y); display.sync()
  mouse_button_down  query_pointer().mask & (Button1Mask | Button2Mask | Button3Mask)
  last_input_tick    XScreenSaver extension idle time (MIT-SCREEN-SAVER)
  focus_screen       _NET_CLIENT_LIST_STACKING (bottom-to-top) -> topmost normal window on that
                     monitor -> send _NET_ACTIVE_WINDOW client message (what wmctrl -a does)
  GlobalHotkey       XGrabKey on the root window
  autostart          ~/.config/autostart/lookhop.desktop

Wayland: compositors deliberately block moving the pointer and activating
other apps' windows from a regular client. Support would need per-compositor
work (e.g. KWin/GNOME Shell scripts, or the RemoteDesktop portal). Detect it
via $XDG_SESSION_TYPE == "wayland" and explain the limitation to the user.
"""
from __future__ import annotations

from lookhop.platform._unsupported import NoHotkey as GlobalHotkey
from lookhop.platform._unsupported import NotPortedYet, open_file
from lookhop.platform._unsupported import tk_message_box as message_box

NAME = "Linux"
SUPPORTED = False


def _todo(what):
    def fn(*_a, **_k):
        raise NotPortedYet(what, NAME)
    return fn


make_dpi_aware = lambda: None  # noqa: E731
list_screens = _todo("list_screens")
get_cursor = _todo("get_cursor")
set_cursor = _todo("set_cursor")
mouse_button_down = _todo("mouse_button_down")
last_input_tick = _todo("last_input_tick")
focus_screen = _todo("focus_screen")
autostart_enabled = lambda: False  # noqa: E731
set_autostart = _todo("set_autostart")
acquire_single_instance = lambda app_name: object()  # noqa: E731


def parse_hotkey(spec: str):
    return spec


__all__ = ["NAME", "SUPPORTED", "acquire_single_instance", "autostart_enabled", "focus_screen",
           "get_cursor", "GlobalHotkey", "last_input_tick", "list_screens", "make_dpi_aware",
           "message_box", "mouse_button_down", "open_file", "parse_hotkey", "set_autostart",
           "set_cursor"]
