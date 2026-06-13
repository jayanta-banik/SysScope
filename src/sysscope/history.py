from __future__ import annotations

from collections import defaultdict, deque

from sysscope.models import MetricSnapshot




class MetricHistory:
    def __init__(self, history_seconds: int, refresh_interval_ms: int) -> None:
        self.max_points = max(2, int(history_seconds * 1000 / refresh_interval_ms))
        self.cpu = deque(maxlen=self.max_points)
        self.memory = deque(maxlen=self.max_points)
        self.gpu_utilization: dict[int, deque[float]] = defaultdict(self._new_series)
        self.gpu_memory: dict[int, deque[float]] = defaultdict(self._new_series)

    def _new_series(self) -> deque[float]:
        return deque(maxlen=self.max_points)

    def append(self, snapshot: MetricSnapshot) -> None:
        self.cpu.append(snapshot.cpu.utilization_percent)
        self.memory.append(snapshot.memory.utilization_percent)
        for gpu in snapshot.gpus:
            self.gpu_utilization[gpu.index].append(gpu.utilization_percent)
            memory_percent = (
                (gpu.memory_used_bytes / gpu.memory_total_bytes) * 100
                if gpu.memory_total_bytes
                else 0.0
            )
            self.gpu_memory[gpu.index].append(memory_percent)

