"""
Pattern detection for configurable routines (KBD, wavu, etc.).
Sliding window over input history; reports match and consecutive count.
Add new routines by inserting an entry into the ROUTINES dict.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from history import InputHistory
    from scoring import Scoring

ROUTINES: dict[str, tuple[str, ...]] = {
    "KBD":  ('b', 'n', 'b', 'db'),
    "Wavu": ('f', 'n', 'd', 'df', 'n'),
}

DEFAULT_ROUTINE = "KBD"


def _count_tail_cycles(segments: list[tuple[str, int]], pattern: Sequence[str]) -> int:
    """
    Count how many full repetitions of the pattern appear at the tail of segments.
    Only complete cycles are counted: if the last cycle is partial (e.g. 5 done,
    6th half done), we return 5, not 0. We do this by trying to ignore 0..n-1
    trailing segments and taking the maximum count of full cycles in the remainder.
    """
    n = len(pattern)
    if n == 0 or not segments:
        return 0

    def count_from_tail(seg_list: list[tuple[str, int]]) -> int:
        cnt = 0
        i = len(seg_list) - 1
        while i >= n - 1:
            for j in range(n):
                if seg_list[i - j][0] != pattern[n - 1 - j]:
                    return cnt
            cnt += 1
            i -= n
        return cnt

    best = 0
    for k in range(n):
        tail = segments[: len(segments) - k] if k else segments
        if len(tail) < n:
            continue
        best = max(best, count_from_tail(tail))
    return best


class PatternMatcher:
    """Checks input history for the active routine's pattern and updates scoring."""

    def __init__(self, history: InputHistory, scoring: Scoring, routine: str = DEFAULT_ROUTINE) -> None:
        self._history = history
        self._scoring = scoring
        self._pattern = ROUTINES[routine]
        self._last_cycles = 0

    def set_routine(self, name: str) -> None:
        """Switch to a different routine pattern and reset cycle tracking."""
        self._pattern = ROUTINES[name]
        self._last_cycles = 0

    def reset(self) -> None:
        """Clear cycle tracking. Call when history is cleared."""
        self._last_cycles = 0

    def update(self) -> None:
        """Run after history is updated. Check tail for the active pattern."""
        segs = self._history.segments_list()
        cycles = _count_tail_cycles(segs, self._pattern)

        if cycles > 0 and cycles >= self._last_cycles:
            self._scoring.record_consecutive(cycles)
            if cycles > self._last_cycles:
                self._scoring.record_success()
        else:
            self._scoring.reset_streak()

        self._last_cycles = cycles
