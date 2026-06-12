from sysscope.config import AppConfig, ConfigStore
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

