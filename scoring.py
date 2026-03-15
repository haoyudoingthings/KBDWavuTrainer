"""
Streak tracking and per-routine high scores with optional JSON persistence.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Optional, Union

from config import DEFAULT_ROUTINE, FREQUENCY_WINDOW_SEC, SCORES_FILENAME


def _scores_path() -> Path:
    return Path(__file__).resolve().parent / SCORES_FILENAME


class Scoring:
    """Tracks current streak, per-routine high scores, and success frequency."""

    def __init__(self, persist_path: Optional[Union[Path, str]] = None,
                 routine: str = DEFAULT_ROUTINE) -> None:
        self._persist_path = Path(persist_path) if persist_path else _scores_path()
        self._routine = routine
        self._current = 0
        self._high_scores: dict[str, int] = {}
        self._times: deque[float] = deque()
        self._load()

    @property
    def routine(self) -> str:
        return self._routine

    def set_routine(self, name: str) -> None:
        self._routine = name
        self._current = 0
        self._times.clear()

    def record_consecutive(self, count: int) -> None:
        self._current = count
        if count > self._high_scores.get(self._routine, 0):
            self._high_scores[self._routine] = count

    def record_success(self) -> None:
        self._times.append(time.perf_counter())
        self._prune_times()

    def reset_streak(self) -> None:
        self._current = 0

    def current(self) -> int:
        return self._current

    def high(self, routine: Optional[str] = None) -> int:
        return self._high_scores.get(routine or self._routine, 0)

    def per_minute(self) -> float:
        self._prune_times()
        if not self._times:
            return 0.0
        span = time.perf_counter() - self._times[0]
        if span <= 0:
            return 0.0
        return len(self._times) / (span / 60.0)

    def reset_session(self) -> None:
        self._current = 0
        self._times.clear()

    def save(self) -> None:
        try:
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(self._high_scores, f)
        except OSError:
            pass

    def _prune_times(self) -> None:
        now = time.perf_counter()
        while self._times and now - self._times[0] > FREQUENCY_WINDOW_SEC:
            self._times.popleft()

    def _load(self) -> None:
        if not self._persist_path.is_file():
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, int) and v > self._high_scores.get(k, 0):
                        self._high_scores[k] = v
        except (OSError, json.JSONDecodeError, TypeError):
            pass
