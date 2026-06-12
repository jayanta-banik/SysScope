from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppConfig:
    always_on_top: bool = True
    start_minimized: bool = False
    compact_mode: bool = True
    clock_24_hour: bool = True
    refresh_interval_ms: int = 1000
    history_seconds: int = 60
    theme: str = "dark_futuristic_hud"
    metrics_source: str = "host"
    window_width: int = 420
    window_height: int = 300

    @classmethod
    def from_mapping(cls, data: Any) -> AppConfig:
        if not isinstance(data, dict):
            return cls()

        defaults = cls()
        values: dict[str, Any] = {}
        bool_fields = {
            "always_on_top",
            "start_minimized",
            "compact_mode",
            "clock_24_hour",
        }
        int_ranges = {
            "refresh_interval_ms": (250, 10_000),
            "history_seconds": (10, 600),
            "window_width": (300, 3000),
            "window_height": (180, 2000),
        }
        for item in fields(cls):
            value = data.get(item.name, getattr(defaults, item.name))
            if item.name in bool_fields and isinstance(value, bool):
                values[item.name] = value
            elif item.name in int_ranges and isinstance(value, int):
                minimum, maximum = int_ranges[item.name]
                values[item.name] = value if minimum <= value <= maximum else getattr(defaults, item.name)
            elif item.name == "theme":
                values[item.name] = (
                    value if value == "dark_futuristic_hud" else defaults.theme
                )
            elif item.name == "metrics_source" and isinstance(value, str):
                values[item.name] = value if value == "host" or value.startswith("wsl:") else "host"
            elif item.name not in bool_fields | set(int_ranges) | {"theme", "metrics_source"}:
                values[item.name] = value
        return cls(**values)

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


def default_config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config.json"
    return Path.cwd() / "config.json"


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return AppConfig()
        return AppConfig.from_mapping(data)

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(config.to_mapping(), indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

