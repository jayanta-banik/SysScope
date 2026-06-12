from __future__ import annotations

import time
from types import ModuleType

from sysscope.models import CpuMetrics, GpuMetrics, MemoryMetrics, MetricSnapshot


class NativeCollector:
    paced = False

    def __init__(
        self,
        psutil_module: ModuleType | None = None,
        nvml_module: ModuleType | None = None,
    ) -> None:
        if psutil_module is None:
            import psutil as psutil_module

        if nvml_module is None:
            try:
                import pynvml as nvml_module
            except ImportError:
                nvml_module = None

        self._psutil = psutil_module
        self._nvml = nvml_module
        self._nvml_ready = False
        if self._nvml is not None:
            try:
                self._nvml.nvmlInit()
                self._nvml_ready = True
            except Exception:
                self._nvml_ready = False

        self._psutil.cpu_percent(interval=None)

    def sample(self) -> MetricSnapshot:
        memory = self._psutil.virtual_memory()
        return MetricSnapshot(
            timestamp=time.time(),
            source_id="host",
            cpu=CpuMetrics(float(self._psutil.cpu_percent(interval=None))),
            memory=MemoryMetrics(
                used_bytes=int(memory.used),
                total_bytes=int(memory.total),
                utilization_percent=float(memory.percent),
            ),
            gpus=tuple(self._gpu_metrics()),
        )

    def _gpu_metrics(self) -> list[GpuMetrics]:
        if not self._nvml_ready or self._nvml is None:
            return []
        result: list[GpuMetrics] = []
        try:
            count = self._nvml.nvmlDeviceGetCount()
            for index in range(count):
                handle = self._nvml.nvmlDeviceGetHandleByIndex(index)
                name = self._nvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode(errors="replace")
                utilization = self._nvml.nvmlDeviceGetUtilizationRates(handle)
                memory = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                try:
                    temperature = self._nvml.nvmlDeviceGetTemperature(
                        handle, self._nvml.NVML_TEMPERATURE_GPU
                    )
                except Exception:
                    temperature = None
                result.append(
                    GpuMetrics(
                        index=index,
                        name=str(name),
                        utilization_percent=float(utilization.gpu),
                        memory_used_bytes=int(memory.used),
                        memory_total_bytes=int(memory.total),
                        temperature_c=(
                            None if temperature is None else float(temperature)
                        ),
                    )
                )
        except Exception:
            return []
        return result

    def stop(self) -> None:
        if self._nvml_ready and self._nvml is not None:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass
            self._nvml_ready = False

