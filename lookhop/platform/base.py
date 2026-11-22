"""OS-independent display helpers shared by every platform backend."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Screen:
    name: str
    left: int
    top: int
    right: int
    bottom: int
    primary: bool

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[int, int]:
        return self.left + self.width // 2, self.top + self.height // 2

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom


def resolve_roles(screens: list[Screen], laptop_display: str) -> tuple[Screen | None, Screen | None]:
    """Return (laptop, monitor). monitor is None when only one display is connected."""
    if not screens:
        return None, None
    key = laptop_display.strip().lower()
    if key == "right":
        laptop = max(screens, key=lambda s: s.right)
    elif key == "primary":
        laptop = next((s for s in screens if s.primary), screens[0])
    elif key == "left":
        laptop = min(screens, key=lambda s: s.left)
    else:
        laptop = next((s for s in screens if s.name.lower() == key),
                      min(screens, key=lambda s: s.left))
    others = [s for s in screens if s != laptop]
    monitor = max(others, key=lambda s: s.area) if others else None
    return laptop, monitor


def screen_at(screens: list[Screen], x: int, y: int) -> Screen | None:
    return next((s for s in screens if s.contains(x, y)), None)
