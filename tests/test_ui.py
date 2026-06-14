from PySide6.QtCore import Qt

from sysscope.config import AppConfig, ConfigStore
from sysscope.models import CpuMetrics, GpuMetrics, MemoryMetrics, MetricSnapshot
from sysscope.timekeeping import TimeMode
from sysscope.ui.main_window import MainWindow


def test_clock_is_default_and_reset_restores_it(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(MainWindow, "_build_tray", lambda self: None)
    monkeypatch.setattr(MainWindow, "switch_source", lambda self, source_id, persist=False: None)
    window = MainWindow(ConfigStore(tmp_path / "config.json"), AppConfig())
    qtbot.addWidget(window)

    assert window.timekeeper.mode is TimeMode.CLOCK
    assert not window.session_controls.isVisible()

    window._start_stopwatch()
    assert window.timekeeper.mode is TimeMode.STOPWATCH
    assert not window.time_label.text().endswith("AM")

    window._reset_session()
    assert window.timekeeper.mode is TimeMode.CLOCK


def test_compact_mode_hides_graphs(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(MainWindow, "_build_tray", lambda self: None)
    monkeypatch.setattr(MainWindow, "switch_source", lambda self, source_id, persist=False: None)
    window = MainWindow(ConfigStore(tmp_path / "config.json"), AppConfig(compact_mode=True))
    qtbot.addWidget(window)
    window.show()

    assert window.expanded_panel.isHidden()
    window._set_compact(False, persist=False)
    assert window.expanded_panel.isVisible()



def make_snapshot(value: float) -> MetricSnapshot:
    return MetricSnapshot(
        timestamp=value,
        source_id="host",
        cpu=CpuMetrics(value),
        memory=MemoryMetrics(int(value), 100, value),
        gpus=(GpuMetrics(0, "GPU", value, int(value), 100, 40),),
    )


def test_font_scale_is_bounded_and_shortcuts_are_registered(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(MainWindow, "_build_tray", lambda self: None)
    monkeypatch.setattr(MainWindow, "switch_source", lambda self, source_id, persist=False: None)
    window = MainWindow(ConfigStore(tmp_path / "config.json"), AppConfig())
    qtbot.addWidget(window)

    shortcut_keys = {shortcut.key().toString() for shortcut in window._font_shortcuts}
    assert {"Ctrl++", "Ctrl+=", "Ctrl+-"}.issubset(shortcut_keys)

    window._set_font_scale(999, persist=False)
    assert window.config.font_scale_percent == 160
    window._increase_font_scale()
    assert window.config.font_scale_percent == 160

    window._set_font_scale(1, persist=False)
    assert window.config.font_scale_percent == 80
    window._decrease_font_scale()
    assert window.config.font_scale_percent == 80


def test_menu_button_exposes_shared_menu(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(MainWindow, "_build_tray", lambda self: None)
    monkeypatch.setattr(MainWindow, "switch_source", lambda self, source_id, persist=False: None)
    window = MainWindow(ConfigStore(tmp_path / "config.json"), AppConfig())
    qtbot.addWidget(window)

    assert window.menu_button.text() == "Menu"
    assert window.menu_button.toolTip() == "Open SysScope menu"
    assert "Font Size" in {action.text() for action in window._create_menu().actions()}


def test_metric_cards_receive_moving_usage_history(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(MainWindow, "_build_tray", lambda self: None)
    monkeypatch.setattr(MainWindow, "switch_source", lambda self, source_id, persist=False: None)
    window = MainWindow(ConfigStore(tmp_path / "config.json"), AppConfig())
    qtbot.addWidget(window)

    window._apply_snapshot(make_snapshot(10))
    window._apply_snapshot(make_snapshot(40))

    assert window.cpu_card._series == (10.0, 40.0)
    assert window.memory_card._series == (10.0, 40.0)
    assert window.gpu_cards[0]._series == (10.0, 40.0)
