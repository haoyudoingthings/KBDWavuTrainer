"""
XInput controller polling and mapping to 8 directions + neutral.
Polls at 60 FPS and invokes a callback with current direction.
"""
import threading
import time
from typing import Callable, Optional

try:
    import XInput
except ImportError:
    XInput = None  # type: ignore

# 8 directions + neutral (Tekken notation)
DIRECTIONS = ("b", "f", "u", "d", "db", "df", "ub", "uf")
# Stick threshold for cardinal vs diagonal (magnitude already normalized by XInput)
STICK_THRESHOLD = 0.35


def _stick_to_direction(lx: float, ly: float) -> Optional[str]:
    """Map left stick (lx, ly) in [-1, 1] to direction string or None if neutral."""
    if XInput is None:
        return None
    # XInput: left = negative X, right = positive X; up = positive Y, down = negative Y
    if abs(lx) < STICK_THRESHOLD and abs(ly) < STICK_THRESHOLD:
        return None
    # Prefer diagonals when both axes are significant
    dx = 1 if lx > STICK_THRESHOLD else (-1 if lx < -STICK_THRESHOLD else 0)
    dy = 1 if ly > STICK_THRESHOLD else (-1 if ly < -STICK_THRESHOLD else 0)
    if dx == 0 and dy == 0:
        return None
    if dx == -1 and dy == 0:
        return "b"
    if dx == 1 and dy == 0:
        return "f"
    if dx == 0 and dy == 1:
        return "u"
    if dx == 0 and dy == -1:
        return "d"
    if dx == -1 and dy == -1:
        return "db"
    if dx == 1 and dy == -1:
        return "df"
    if dx == -1 and dy == 1:
        return "ub"
    if dx == 1 and dy == 1:
        return "uf"
    return None


def _dpad_to_direction(buttons: dict) -> Optional[str]:
    """Map D-pad buttons to direction. Prefer stick; use D-pad if no stick direction."""
    u = buttons.get("DPAD_UP", False)
    d = buttons.get("DPAD_DOWN", False)
    l = buttons.get("DPAD_LEFT", False)
    r = buttons.get("DPAD_RIGHT", False)
    if l and not r and not u and not d:
        return "b"
    if r and not l and not u and not d:
        return "f"
    if u and not d and not l and not r:
        return "u"
    if d and not u and not l and not r:
        return "d"
    if l and d and not r and not u:
        return "db"
    if r and d and not l and not u:
        return "df"
    if l and u and not r and not d:
        return "ub"
    if r and u and not l and not d:
        return "uf"
    return None


class ControllerReader:
    """Polls first connected XInput controller at 60 FPS and reports current direction."""

    def __init__(self, user_index: int = 0):
        self._user_index = user_index
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_callback: Optional[Callable[[], None]] = None
        self._last_direction: Optional[str] = None

    def get_current_direction(self) -> Optional[str]:
        """Return current 8-way direction from left stick or D-pad, or None if neutral."""
        if XInput is None:
            return None
        try:
            state = XInput.get_state(self._user_index)
        except (XInput.XInputNotConnectedError, XInput.XInputBadArgumentError):
            return None
        (lx, ly), _ = XInput.get_thumb_values(state)
        direction = _stick_to_direction(lx, ly)
        if direction is None:
            buttons = XInput.get_button_values(state)
            direction = _dpad_to_direction(buttons)
        return direction

    def start_polling(self, on_tick: Callable[[], None]) -> None:
        """Start background thread that polls at ~60 FPS and calls on_tick each frame."""
        if self._running:
            return
        self._poll_callback = on_tick
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self) -> None:
        """Stop the polling thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None
        self._poll_callback = None

    def _poll_loop(self) -> None:
        interval = 1.0 / 60.0
        while self._running:
            start = time.perf_counter()
            if self._poll_callback:
                self._poll_callback()
            elapsed = time.perf_counter() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
