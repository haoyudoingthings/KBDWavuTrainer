"""
Input history: bounded deque of (direction, duration_frames).
When direction changes, finalize the previous segment and start a new one.
Assumes 60 FPS (one tick = one frame).
"""
from collections import deque
from typing import Iterator, Optional, Tuple


class InputHistory:
    """Stores recent input segments (direction, duration_frames) with a max capacity."""

    def __init__(self, max_segments: int = 300):
        self._segments: deque[tuple[str, int]] = deque(maxlen=max_segments)
        self._current_direction: Optional[str] = None
        self._current_frames: int = 0

    def tick(self, direction: Optional[str]) -> None:
        """
        Call once per frame (60 FPS). If direction changed, push previous segment
        and start a new one. If same direction, increment frame count.
        """
        if direction is None:
            if self._current_direction is not None:
                self._push_current()
            self._current_direction = None
            self._current_frames = 0
            return
        if direction == self._current_direction:
            self._current_frames += 1
            return
        self._push_current()
        self._current_direction = direction
        self._current_frames = 1

    def _push_current(self) -> None:
        if self._current_direction is not None and self._current_frames > 0:
            self._segments.append((self._current_direction, self._current_frames))

    def segments(self) -> Iterator[tuple[str, int]]:
        """Iterate over (direction, duration_frames), oldest first. Excludes current in-progress segment."""
        yield from self._segments

    def segments_list(self) -> list[tuple[str, int]]:
        """Return a copy of segments (oldest first)."""
        return list(self._segments)

    def current_segment(self) -> Tuple[Optional[str], int]:
        """Current direction and its frame count so far (may not be pushed yet)."""
        return (self._current_direction, self._current_frames)

    def clear(self) -> None:
        """Clear all segments and current state."""
        self._segments.clear()
        self._current_direction = None
        self._current_frames = 0
