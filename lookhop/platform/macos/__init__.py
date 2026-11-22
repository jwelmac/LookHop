"""macOS backend - NOT IMPLEMENTED YET (help wanted!).

Everything else in LookHop (camera, face tracking, calibration, control panel,
tray) is cross-platform already. To port it, implement the functions below and
set SUPPORTED = True. Suggested APIs (via pyobjc: pyobjc-framework-Quartz,
pyobjc-framework-Cocoa):

  list_screens       NSScreen.screens() -> frames (flip Y: Cocoa origin is bottom-left)
                     or Quartz.CGGetActiveDisplayList + CGDisplayBounds (top-left origin)
  get_cursor         Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
  set_cursor         Quartz.CGWarpMouseCursorPosition((x, y))
                     + CGAssociateMouseAndMouseCursorPosition(True)
  mouse_button_down  Quartz.CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, btn)
  last_input_tick    Quartz.CGEventSourceSecondsSinceLastEventType(..., kCGAnyInputEventType)
                     (return a value that changes on keyboard/click input)
  focus_screen       CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly) is front-to-back;
                     pick the first normal-layer window whose bounds sit on that screen, then
                     NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                       .activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
  GlobalHotkey       Carbon RegisterEventHotKey, or a Quartz event tap
  autostart          a LaunchAgent plist in ~/Library/LaunchAgents
  make_dpi_aware     nothing to do (Quartz uses points everywhere)

Permissions the user must grant: Camera, Accessibility (cursor + focus),
and possibly Input Monitoring (hotkey / typing detection).
"""
from __future__ import annotations

from lookhop.platform._unsupported import NoHotkey as GlobalHotkey
from lookhop.platform._unsupported import NotPortedYet, open_file
from lookhop.platform._unsupported import tk_message_box as message_box

NAME = "macOS"
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
