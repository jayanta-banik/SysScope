from __future__ import annotations

import threading
import time
from collections.abc import Callable

from PySide6.QtCore import QThread, Signal

from sysscope.collectors.base import MetricsCollector
from sysscope.collectors.native import NativeCollector
from sysscope.collectors.wsl import WslCollector


def create_collector(source_id: str, refresh_interval_ms: int) -> MetricsCollector:
    if source_id.startswith("wsl:"):
        return WslCollector(source_id.removeprefix("wsl:"), refresh_interval_ms)
    return NativeCollector()


class MetricsThread(QThread):
    snapshotReady = Signal(object)
    sourceError = Signal(str)
    fallbackRequested = Signal()

    def __init__(
        self,
        source_id: str,
        refresh_interval_ms: int,
        factory: Callable[[str, int], MetricsCollector] = create_collector,
    ) -> None:
        super().__init__()
        self.source_id = source_id
        self.refresh_interval_ms = refresh_interval_ms
        self._factory = factory
        self._stop_event = threading.Event()
        self._collector: MetricsCollector | None = None

    def run(self) -> None:
        try:
            self._collector = self._factory(self.source_id, self.refresh_interval_ms)
            while not self._stop_event.is_set():
                started = time.monotonic()
                try:
                    self.snapshotReady.emit(self._collector.sample())
                except Exception as error:
                    self.sourceError.emit(str(error))
                    if self.source_id.startswith("wsl:"):
                        self.fallbackRequested.emit()
                        break
                if not self._collector.paced:
                    elapsed = time.monotonic() - started
                    wait_seconds = max(0.0, self.refresh_interval_ms / 1000 - elapsed)
                    self._stop_event.wait(wait_seconds)
        finally:
            if self._collector is not None:
                self._collector.stop()
                self._collector = None

    def request_stop(self) -> None:
        self._stop_event.set()
        if self._collector is not None:
            self._collector.stop()

