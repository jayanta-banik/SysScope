from types import SimpleNamespace

from sysscope.collectors.native import NativeCollector


class FakePsutil:
    def cpu_percent(self, interval=None):
        return 42.0

    def virtual_memory(self):
        return SimpleNamespace(used=25, total=100, percent=25.0)


class FakeNvml:
    NVML_TEMPERATURE_GPU = 0

    def nvmlInit(self):
        pass

    def nvmlShutdown(self):
        pass

    def nvmlDeviceGetCount(self):
        return 2

    def nvmlDeviceGetHandleByIndex(self, index):
        return index

    def nvmlDeviceGetName(self, handle):
        return f"GPU {handle}".encode()

    def nvmlDeviceGetUtilizationRates(self, handle):
        return SimpleNamespace(gpu=10 + handle)

    def nvmlDeviceGetMemoryInfo(self, handle):
        return SimpleNamespace(used=20 + handle, total=100)

    def nvmlDeviceGetTemperature(self, handle, sensor):
        return 40 + handle


class BrokenNvml(FakeNvml):
    def nvmlInit(self):
        raise RuntimeError("No driver")


def test_native_collector_returns_normalized_multi_gpu_snapshot():
    collector = NativeCollector(FakePsutil(), FakeNvml())

    result = collector.sample()

    assert result.source_id == "host"
    assert result.cpu.utilization_percent == 42
    assert result.memory.used_bytes == 25
    assert [gpu.name for gpu in result.gpus] == ["GPU 0", "GPU 1"]


def test_native_collector_gracefully_handles_missing_nvml():
    collector = NativeCollector(FakePsutil(), BrokenNvml())

    assert collector.sample().gpus == ()

