"""
Input history: bounded deque of (direction, duration_frames).
When direction changes, finalize the previous segment and start a new one.
Assumes 60 FPS (one tick = one frame).
"""
from __future__ import annotations

from collections import deque
from typing import Iterator, Optional

from config import MAX_SEGMENTS


class InputHistory:
    """Stores recent input segments (direction, duration_frames) with a max capacity."""

    def __init__(self, max_segments: int = MAX_SEGMENTS):
        self._segments: deque[tuple[str, int]] = deque(maxlen=max_segments)
        self._current_direction: Optional[str] = None
        self._current_frames: int = 0

    def tick(self, direction: Optional[str]) -> None:
        effective = "n" if direction is None else direction
        if effective == self._current_direction:
            self._current_frames += 1
            return
        self._push_current()
        self._current_direction = effective
        self._current_frames = 1

    def _push_current(self) -> None:
        if self._current_direction is not None and self._current_frames > 0:
            self._segments.append((self._current_direction, self._current_frames))

    @staticmethod
    def is_neutral(direction: Optional[str]) -> bool:
        return direction is None or direction == "n"

    def segments(self) -> Iterator[tuple[str, int]]:
        yield from self._segments

    def segments_list(self) -> list[tuple[str, int]]:
        return list(self._segments)

    def current_segment(self) -> tuple[Optional[str], int]:
        return (self._current_direction, self._current_frames)

    def clear(self) -> None:
        self._segments.clear()
        self._current_direction = None
        self._current_frames = 0
