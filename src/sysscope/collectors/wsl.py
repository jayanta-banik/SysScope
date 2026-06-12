from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from typing import IO, Any

from sysscope.models import MetricSnapshot


WSL_PROBE_SCRIPT = r"""
import json
import subprocess
import sys
import time

interval = max(0.25, float(sys.argv[1]))

def cpu_values():
    fields = open("/proc/stat", encoding="utf-8").readline().split()[1:]
    values = [int(value) for value in fields]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle

def memory_values():
    values = {}
    with open("/proc/meminfo", encoding="utf-8") as stream:
        for line in stream:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0]) * 1024
    total = values["MemTotal"]
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = total - available
    return used, total

def gpu_values():
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        lines = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).splitlines()
    except Exception:
        return []
    result = []
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 6:
            continue
        try:
            result.append({
                "index": int(parts[0]),
                "name": parts[1],
                "utilization_percent": float(parts[2]),
                "memory_used_bytes": int(float(parts[3]) * 1024 * 1024),
                "memory_total_bytes": int(float(parts[4]) * 1024 * 1024),
                "temperature_c": float(parts[5]),
            })
        except ValueError:
            continue
    return result

previous_total, previous_idle = cpu_values()
while True:
    time.sleep(interval)
    total, idle = cpu_values()
    delta_total = max(1, total - previous_total)
    utilization = 100.0 * (1.0 - ((idle - previous_idle) / delta_total))
    previous_total, previous_idle = total, idle
    memory_used, memory_total = memory_values()
    payload = {
        "timestamp": time.time(),
        "cpu": {"utilization_percent": utilization},
        "memory": {
            "used_bytes": memory_used,
            "total_bytes": memory_total,
            "utilization_percent": (memory_used / memory_total) * 100.0,
        },
        "gpus": gpu_values(),
    }
    print(json.dumps(payload, separators=(",", ":")), flush=True)
"""


def _default_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(*args, **kwargs)


def discover_wsl_distributions(
    runner: Callable[..., subprocess.CompletedProcess[str]] = _default_runner,
) -> list[str]:
    try:
        result = runner(
            ["wsl.exe", "--list", "--quiet"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [
        line.strip()
        for line in result.stdout.replace("\x00", "").splitlines()
        if line.strip()
    ]


class WslCollector:
    paced = True

    def __init__(
        self,
        distribution: str,
        refresh_interval_ms: int = 1000,
        popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ) -> None:
        self.distribution = distribution
        self.source_id = f"wsl:{distribution}"
        self._popen = popen
        self._interval_seconds = refresh_interval_ms / 1000
        self._process: subprocess.Popen[str] | None = None

    def _start(self) -> None:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._process = self._popen(
            [
                "wsl.exe",
                "-d",
                self.distribution,
                "--",
                "python3",
                "-u",
                "-c",
                WSL_PROBE_SCRIPT,
                str(self._interval_seconds),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )

    def sample(self) -> MetricSnapshot:
        if self._process is None:
            self._start()
        assert self._process is not None
        stdout: IO[str] | None = self._process.stdout
        if stdout is None:
            raise RuntimeError("WSL probe did not expose stdout")
        line = stdout.readline()
        if not line:
            message = "WSL probe stopped unexpectedly"
            if self._process.stderr is not None:
                detail = self._process.stderr.read().strip()
                if detail:
                    message = f"{message}: {detail}"
            raise RuntimeError(message)
        try:
            payload = json.loads(line)
            return MetricSnapshot.from_mapping(payload, self.source_id)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError("WSL probe returned malformed metrics") from error

    def stop(self) -> None:
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

