from sysscope.history import MetricHistory
from sysscope.models import CpuMetrics, GpuMetrics, MemoryMetrics, MetricSnapshot


def snapshot(value: float) -> MetricSnapshot:
    return MetricSnapshot(
        timestamp=value,
        source_id="host",
        cpu=CpuMetrics(value),
        memory=MemoryMetrics(50, 100, value),
        gpus=(GpuMetrics(0, "GPU", value, int(value), 100, 40),),
    )


def test_history_is_bounded_for_all_series():
    history = MetricHistory(history_seconds=2, refresh_interval_ms=1000)

    for value in range(5):
        history.append(snapshot(float(value)))

    assert list(history.cpu) == [3.0, 4.0]
    assert list(history.memory) == [3.0, 4.0]
    assert list(history.gpu_utilization[0]) == [3.0, 4.0]
    assert list(history.gpu_memory[0]) == [3.0, 4.0]

