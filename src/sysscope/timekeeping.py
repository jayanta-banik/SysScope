from __future__ import annotations

import math
import time
from enum import Enum
from typing import Callable


class TimeMode(str, Enum):
    CLOCK = "clock"
    STOPWATCH = "stopwatch"
    TIMER = "timer"


class Timekeeper:
    def __init__(self, now: Callable[[], float] = time.monotonic) -> None:
        self._now = now
        self.mode = TimeMode.CLOCK
        self.paused = False
        self._started_at = 0.0
        self._accumulated = 0.0
        self._duration = 0.0

    @property
    def active(self) -> bool:
        return self.mode is not TimeMode.CLOCK

    def start_stopwatch(self) -> None:
        self.mode = TimeMode.STOPWATCH
        self.paused = False
        self._started_at = self._now()
        self._accumulated = 0.0
        self._duration = 0.0

    def start_timer(self, duration_seconds: float) -> None:
        if duration_seconds <= 0:
            raise ValueError("Timer duration must be positive")
        self.mode = TimeMode.TIMER
        self.paused = False
        self._started_at = self._now()
        self._accumulated = 0.0
        self._duration = float(duration_seconds)

    def pause(self) -> None:
        if not self.active or self.paused:
            return
        self._accumulated = self.elapsed_seconds()
        self.paused = True

    def resume(self) -> None:
        if not self.active or not self.paused or self.finished:
            return
        self._started_at = self._now()
        self.paused = False

    def reset(self) -> None:
        self.mode = TimeMode.CLOCK
        self.paused = False
        self._started_at = 0.0
        self._accumulated = 0.0
        self._duration = 0.0

    def elapsed_seconds(self) -> float:
        if not self.active:
            return 0.0
        elapsed = self._accumulated
        if not self.paused:
            elapsed += self._now() - self._started_at
        return max(0.0, elapsed)

    @property
    def finished(self) -> bool:
        return self.mode is TimeMode.TIMER and self.elapsed_seconds() >= self._duration

    def display_text(self) -> str:
        if self.mode is TimeMode.STOPWATCH:
            milliseconds = round(self.elapsed_seconds() * 1000)
            hours, remainder = divmod(milliseconds, 3_600_000)
            minutes, remainder = divmod(remainder, 60_000)
            seconds, millis = divmod(remainder, 1000)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
        if self.mode is TimeMode.TIMER:
            remaining = max(0, math.ceil(self._duration - self.elapsed_seconds()))
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return ""

