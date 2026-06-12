import json

from sysscope.config import AppConfig, ConfigStore


def test_missing_config_uses_defaults(tmp_path):
    config = ConfigStore(tmp_path / "config.json").load()

    assert config == AppConfig()


def test_invalid_values_fall_back_independently(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "always_on_top": False,
                "refresh_interval_ms": 2,
                "history_seconds": 120,
                "theme": "unknown",
                "metrics_source": "wsl:Ubuntu",
            }
        ),
        encoding="utf-8",
    )

    config = ConfigStore(path).load()

    assert config.always_on_top is False
    assert config.refresh_interval_ms == 1000
    assert config.history_seconds == 120
    assert config.theme == "dark_futuristic_hud"
    assert config.metrics_source == "wsl:Ubuntu"


def test_config_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    expected = AppConfig(compact_mode=False, clock_24_hour=False, window_width=800)

    store.save(expected)

    assert store.load() == expected

