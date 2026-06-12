import io
from types import SimpleNamespace

from sysscope.collectors.wsl import WslCollector, discover_wsl_distributions


def test_discovery_removes_windows_null_characters():
    def runner(*args, **kwargs):
        return SimpleNamespace(stdout="U\x00b\x00u\x00n\x00t\x00u\x00\nDocker\n")

    assert discover_wsl_distributions(runner) == ["Ubuntu", "Docker"]


class FakeProcess:
    def __init__(self, output: str):
        self.stdout = io.StringIO(output)
        self.stderr = io.StringIO("")
        self.terminated = False

    def poll(self):
        return None if not self.terminated else 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


def test_wsl_collector_parses_normalized_record():
    output = (
        '{"timestamp":1,"cpu":{"utilization_percent":25},'
        '"memory":{"used_bytes":20,"total_bytes":100,"utilization_percent":20},'
        '"gpus":[{"index":0,"name":"GPU","utilization_percent":50,'
        '"memory_used_bytes":40,"memory_total_bytes":100,"temperature_c":42}]}\n'
    )
    process = FakeProcess(output)
    collector = WslCollector("Ubuntu", popen=lambda *args, **kwargs: process)

    result = collector.sample()

    assert result.source_id == "wsl:Ubuntu"
    assert result.cpu.utilization_percent == 25
    assert result.gpus[0].temperature_c == 42
    collector.stop()
    assert process.terminated


def test_wsl_collector_rejects_malformed_record():
    collector = WslCollector("Ubuntu", popen=lambda *args, **kwargs: FakeProcess("{}\n"))

    try:
        collector.sample()
    except RuntimeError as error:
        assert "malformed" in str(error)
    else:
        raise AssertionError("Expected malformed metrics to be rejected")

