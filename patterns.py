"""
Pattern detection for KBD (Korean Back Dash) and wavu (wave dash).
Sliding window over input history; reports match and consecutive count.
Sequences are tuples of direction symbols (e.g. 'b', 'n', 'db'); change
KBD_SEQUENCE / WAVU_SEQUENCE and the rest of the code adapts.
"""
from typing import TYPE_CHECKING, Sequence, Tuple

if TYPE_CHECKING:
    from history import InputHistory
    from scoring import Scoring

# KBD: b n b (db b n b) * n
KBD_SEQUENCE: Tuple[str, ...] = ('b', 'n', 'b', 'db')

# Wavu: f n d df (n f n d df) * n
WAVU_SEQUENCE: Tuple[str, ...] = ('f', 'n', 'd', 'df', 'n')


def _count_tail_cycles(segments: list[tuple[str, int]], pattern: Sequence[str]) -> int:
    """
    Count how many full repetitions of the pattern appear at the tail of segments.
    Pattern can be any length (e.g. 2-step or 4-step). Each "cycle" is one full
    match of the pattern from the end (last segment = last element of pattern).
    """
    n = len(pattern)
    if n == 0 or not segments:
        return 0
    count = 0
    i = len(segments) - 1
    while i >= n - 1:
        for j in range(n):
            if segments[i - j][0] != pattern[n - 1 - j]:
                return count
        count += 1
        i -= n
    return count


def _tail_matches(segments: list[tuple[str, int]], pattern: Sequence[str], min_cycles: int = 1) -> bool:
    """True if the tail has at least min_cycles full repetitions of the pattern."""
    return _count_tail_cycles(segments, pattern) >= min_cycles


class PatternMatcher:
    """Checks input history for KBD and wavu, updates scoring on match."""

    def __init__(self, history: "InputHistory", scoring: "Scoring") -> None:
        self._history = history
        self._scoring = scoring
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
