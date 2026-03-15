"""
Pattern detection for KBD (Korean Back Dash) and wavu (wave dash).
Sliding window over input history; reports match and consecutive count.
Sequences are tuples of direction symbols (e.g. 'b', 'n', 'db'); change
KBD_SEQUENCE / WAVU_SEQUENCE and the rest of the code adapts.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from history import InputHistory
    from scoring import Scoring

# KBD: b n b (db b n b) * n
KBD_SEQUENCE: tuple[str, ...] = ('b', 'n', 'b', 'db')

# Wavu: f n d df (n f n d df) * n
WAVU_SEQUENCE: tuple[str, ...] = ('f', 'n', 'd', 'df', 'n')


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
        """Count full pattern repetitions at the end of seg_list (tail must end with pattern)."""
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


def _tail_matches(segments: list[tuple[str, int]], pattern: Sequence[str], min_cycles: int = 1) -> bool:
    """True if the tail has at least min_cycles full repetitions of the pattern."""
    return _count_tail_cycles(segments, pattern) >= min_cycles


class PatternMatcher:
    """Checks input history for KBD and wavu, updates scoring on match."""

    def __init__(self, history: InputHistory, scoring: Scoring) -> None:
        self._history = history
        self._scoring = scoring
        self._last_kbd_cycles = 0
        self._last_wavu_cycles = 0

    def reset(self) -> None:
        """Clear cycle tracking. Call when history is cleared."""
        self._last_kbd_cycles = 0
        self._last_wavu_cycles = 0

    def update(self) -> None:
        """
        Run after history is updated. Check tail for KBD and wavu;
        update scoring with consecutive counts and record success for frequency.
        """
        segs = self._history.segments_list()
        kbd_cycles = _count_tail_cycles(segs, KBD_SEQUENCE)
        wavu_cycles = _count_tail_cycles(segs, WAVU_SEQUENCE)

        if kbd_cycles > 0:
            self._scoring.record_kbd_consecutive(kbd_cycles)
            if kbd_cycles > self._last_kbd_cycles:
                self._scoring.record_kbd_success()
        else:
            self._scoring.reset_kbd_streak()

        if wavu_cycles > 0:
            self._scoring.record_wavu_consecutive(wavu_cycles)
            if wavu_cycles > self._last_wavu_cycles:
                self._scoring.record_wavu_success()
        else:
            self._scoring.reset_wavu_streak()

        self._last_kbd_cycles = kbd_cycles
        self._last_wavu_cycles = wavu_cycles
