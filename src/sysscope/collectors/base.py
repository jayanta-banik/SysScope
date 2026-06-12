from __future__ import annotations

from typing import Protocol

from sysscope.models import MetricSnapshot


class MetricsCollector(Protocol):
    paced: bool

    def sample(self) -> MetricSnapshot: ...

    def stop(self) -> None: ...

