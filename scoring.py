"""
Current and highest streak per technique (KBD, wavu), plus frequency (e.g. per minute).
Optional persistence to JSON.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional, Union

# Default path for saving high scores (in user's app data or next to script)
def _scores_path() -> Path:
    base = Path(__file__).resolve().parent
    return base / "scores.json"

# Rolling window for frequency (seconds)
FREQUENCY_WINDOW_SEC = 60.0


class Scoring:
    """Tracks current/highest streak and frequency for KBD and wavu."""

    def __init__(self, persist_path: Optional[Union[Path, str]] = None) -> None:
        self._persist_path = Path(persist_path) if persist_path else _scores_path()
        # Current streak = consecutive count from pattern matcher (we use the value from matcher)
        self._kbd_current = 0
        self._kbd_high = 0
        self._wavu_current = 0
        self._wavu_high = 0
        # Success timestamps for frequency (per minute)
        self._kbd_times: list[float] = []
        self._wavu_times: list[float] = []
        self._load()

    def record_kbd_consecutive(self, count: int) -> None:
        self._kbd_current = count
        if count > self._kbd_high:
            self._kbd_high = count

    def record_kbd_success(self) -> None:
        self._kbd_times.append(time.perf_counter())
        self._prune_times(self._kbd_times)
        self._save()

    def reset_kbd_streak(self) -> None:
        self._kbd_current = 0

    def record_wavu_consecutive(self, count: int) -> None:
        self._wavu_current = count
        if count > self._wavu_high:
            self._wavu_high = count

    def record_wavu_success(self) -> None:
        self._wavu_times.append(time.perf_counter())
        self._prune_times(self._wavu_times)
        self._save()

    def reset_wavu_streak(self) -> None:
        self._wavu_current = 0

    def _prune_times(self, times: list[float]) -> None:
        now = time.perf_counter()
        while times and now - times[0] > FREQUENCY_WINDOW_SEC:
            times.pop(0)

    def kbd_current(self) -> int:
        return self._kbd_current

    def kbd_high(self) -> int:
        return self._kbd_high

    def wavu_current(self) -> int:
        return self._wavu_current

    def wavu_high(self) -> int:
        return self._wavu_high

    def kbd_per_minute(self) -> float:
        self._prune_times(self._kbd_times)
        if not self._kbd_times:
            return 0.0
        span = time.perf_counter() - self._kbd_times[0]
        if span <= 0:
            return 0.0
        return len(self._kbd_times) / (span / 60.0)

    def wavu_per_minute(self) -> float:
        self._prune_times(self._wavu_times)
        if not self._wavu_times:
            return 0.0
        span = time.perf_counter() - self._wavu_times[0]
        if span <= 0:
            return 0.0
        return len(self._wavu_times) / (span / 60.0)

    def _load(self) -> None:
        if not self._persist_path.is_file():
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._kbd_high = max(self._kbd_high, data.get("kbd_high", 0))
            self._wavu_high = max(self._wavu_high, data.get("wavu_high", 0))
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self) -> None:
        try:
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump({"kbd_high": self._kbd_high, "wavu_high": self._wavu_high}, f)
        except OSError:
            pass
