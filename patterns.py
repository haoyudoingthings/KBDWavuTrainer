"""
Pattern detection for KBD (Korean Back Dash) and wavu (wave dash).
Sliding window over input history; reports match and consecutive count.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from history import InputHistory
    from scoring import Scoring

# KBD: alternating b and db (b -> db -> b -> db ...). One "cycle" = one (b, db) or (db, b).
KBD_SEQUENCE = ("b", "db")

# Wavu: alternating d and df (d -> df -> d -> df ...).
WAVU_SEQUENCE = ("d", "df")


def _count_tail_cycles(segments: list[tuple[str, int]], pattern: tuple[str, str]) -> int:
    """
    Count how many full cycles of the two-step pattern appear at the tail.
    Pattern is (first, second) e.g. ("b", "db"). Counts (first, second) pairs from the end.
    """
    if len(pattern) != 2 or not segments:
        return 0
    first, second = pattern
    count = 0
    i = len(segments) - 1
    while i >= 0:
        if segments[i][0] != second:
            break
        if i == 0:
            break
        if segments[i - 1][0] != first:
            break
        count += 1
        i -= 2
    return count


def _tail_matches(segments: list[tuple[str, int]], pattern: tuple[str, str], min_cycles: int = 1) -> bool:
    """True if the tail has at least min_cycles full cycles of (first, second)."""
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
