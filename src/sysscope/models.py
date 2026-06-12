from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CpuMetrics:
    utilization_percent: float


@dataclass(frozen=True, slots=True)
class MemoryMetrics:
    used_bytes: int
    total_bytes: int
    utilization_percent: float


@dataclass(frozen=True, slots=True)
class GpuMetrics:
    index: int
    name: str
    utilization_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    temperature_c: float | None


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    timestamp: float
    source_id: str
    cpu: CpuMetrics
    memory: MemoryMetrics
    gpus: tuple[GpuMetrics, ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source_id: str) -> MetricSnapshot:
        cpu = data["cpu"]
        memory = data["memory"]
        return cls(
            timestamp=float(data["timestamp"]),
            source_id=source_id,
            cpu=CpuMetrics(utilization_percent=float(cpu["utilization_percent"])),
            memory=MemoryMetrics(
                used_bytes=int(memory["used_bytes"]),
                total_bytes=int(memory["total_bytes"]),
                utilization_percent=float(memory["utilization_percent"]),
            ),
            gpus=tuple(
                GpuMetrics(
                    index=int(gpu["index"]),
                    name=str(gpu["name"]),
                    utilization_percent=float(gpu["utilization_percent"]),
                    memory_used_bytes=int(gpu["memory_used_bytes"]),
                    memory_total_bytes=int(gpu["memory_total_bytes"]),
                    temperature_c=(
                        None
                        if gpu.get("temperature_c") is None
                        else float(gpu["temperature_c"])
                    ),
                )
                for gpu in data.get("gpus", ())
            ),
        )


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    source_id: str
    label: str
    kind: str
    distribution: str | None = None

