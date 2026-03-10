"""
XInput controller polling and mapping to 8 directions + neutral.
Polls at 60 FPS and queues directions for the main thread to consume.
"""
from __future__ import annotations

import queue
import threading
import time
from typing import Optional

try:
    import XInput
except ImportError:
    XInput = None  # type: ignore

DIRECTIONS = ("b", "f", "u", "d", "db", "df", "ub", "uf")
STICK_THRESHOLD = 0.35

_STICK_MAP: dict[tuple[int, int], str] = {
    (-1, 0): "b",
    (1, 0): "f",
    (0, 1): "u",
    (0, -1): "d",
    (-1, -1): "db",
    (1, -1): "df",
    (-1, 1): "ub",
    (1, 1): "uf",
}

_DPAD_MAP: dict[tuple[bool, bool, bool, bool], str] = {
    (False, False, True, False): "b",   # left only
    (False, False, False, True): "f",   # right only
    (True, False, False, False): "u",   # up only
    (False, True, False, False): "d",   # down only
    (False, True, True, False): "db",   # down + left
    (False, True, False, True): "df",   # down + right
    (True, False, True, False): "ub",   # up + left
    (True, False, False, True): "uf",   # up + right
}


def _stick_to_direction(lx: float, ly: float) -> Optional[str]:
    """Map left stick (lx, ly) in [-1, 1] to direction string or None if neutral."""
    if abs(lx) < STICK_THRESHOLD and abs(ly) < STICK_THRESHOLD:
        return None
    dx = 1 if lx > STICK_THRESHOLD else (-1 if lx < -STICK_THRESHOLD else 0)
    dy = 1 if ly > STICK_THRESHOLD else (-1 if ly < -STICK_THRESHOLD else 0)
    return _STICK_MAP.get((dx, dy))


def _dpad_to_direction(buttons: dict) -> Optional[str]:
    """Map D-pad buttons to direction string or None."""
    key = (
        buttons.get("DPAD_UP", False),
        buttons.get("DPAD_DOWN", False),
        buttons.get("DPAD_LEFT", False),
        buttons.get("DPAD_RIGHT", False),
    )
    return _DPAD_MAP.get(key)


class ControllerReader:
    """Polls first connected XInput controller at 60 FPS and queues directions."""

    def __init__(self, user_index: int = 0):
        self._user_index = user_index
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._queue: queue.Queue[Optional[str]] = queue.Queue()

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

    def start_polling(self) -> None:
        """Start background thread that polls at ~60 FPS and queues directions."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self) -> None:
        """Stop the polling thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None

    def drain(self) -> list[Optional[str]]:
        """Return all queued directions since last drain, clearing the queue."""
        items: list[Optional[str]] = []
        while True:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items

    def _poll_loop(self) -> None:
        interval = 1.0 / 60.0
        while self._running:
            start = time.perf_counter()
            self._queue.put(self.get_current_direction())
            elapsed = time.perf_counter() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
