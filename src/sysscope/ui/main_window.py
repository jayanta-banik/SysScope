from __future__ import annotations

import gc
import platform
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QIcon,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from sysscope.collectors.wsl import discover_wsl_distributions
from sysscope.config import AppConfig, ConfigStore
from sysscope.history import MetricHistory
from sysscope.models import GpuMetrics, MetricSnapshot
from sysscope.timekeeping import TimeMode, Timekeeper
from sysscope.worker import MetricsThread


MIN_FONT_SCALE = 80
MAX_FONT_SCALE = 160
FONT_SCALE_STEP = 10


STYLESHEET = """
QWidget {
    background: #071018;
    color: #d8fbff;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}
QWidget#hud {
    border: 1px solid #16cfe0;
    border-radius: 8px;
}
QLabel#timeDisplay {
    color: #5cf5ff;
    font-size: 30px;
    font-weight: 600;
    letter-spacing: 2px;
}
QLabel#sourceLabel, QLabel#statusLabel {
    color: #76a9b0;
    font-size: 10px;
}
QFrame#metricCard {
    background: #0b1b25;
    border: 1px solid #174553;
    border-radius: 6px;
}
QFrame#metricCard QLabel { background: transparent; }
QLabel#metricTitle {
    color: #32ddea;
    font-weight: 600;
}
QPushButton {
    background: #102e39;
    border: 1px solid #20b8c7;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton#menuButton {
    font-weight: 700;
    min-width: 30px;
}
QPushButton:hover { background: #174553; }
QMenu {
    background: #0b1b25;
    border: 1px solid #20b8c7;
}
QMenu::item:selected { background: #174553; }
"""


def build_stylesheet(scale_percent: int) -> str:
    scale = scale_percent / 100
    return (
        STYLESHEET.replace("font-size: 12px;", f"font-size: {round(12 * scale)}px;")
        .replace("font-size: 30px;", f"font-size: {round(30 * scale)}px;")
        .replace("font-size: 10px;", f"font-size: {round(10 * scale)}px;")
    )


def format_bytes(value: int) -> str:
    gib = value / (1024**3)
    return f"{gib:.1f} GiB"


def make_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#071018"))
    painter = QPainter(pixmap)
    painter.setPen(QPen(QColor("#5cf5ff"), 3))
    painter.drawEllipse(5, 5, 22, 22)
    painter.drawLine(16, 8, 16, 17)
    painter.drawLine(16, 17, 23, 17)
    painter.end()
    return QIcon(pixmap)


class MetricCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("metricTitle")
        self.value = QLabel("--")
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        self._series: tuple[float, ...] = ()

    def set_series(self, values) -> None:
        self._series = tuple(float(value) for value in values)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if len(self._series) < 2:
            return

        bounds = self.rect().adjusted(1, 1, -1, -1)
        width = max(1, bounds.width())
        height = max(1, bounds.height())
        step = width / (len(self._series) - 1)
        path = QPainterPath()
        for index, value in enumerate(self._series):
            x = bounds.left() + (index * step)
            y = bounds.bottom() - (max(0.0, min(100.0, value)) / 100 * height)
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        fill = QPainterPath(path)
        fill.lineTo(bounds.right(), bounds.bottom())
        fill.lineTo(bounds.left(), bounds.bottom())
        fill.closeSubpath()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(fill, QBrush(QColor(18, 178, 194, 28)))
        painter.setPen(QPen(QColor(50, 221, 234, 95), 1.5))
        painter.drawPath(path)


class TimerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Start Timer")
        layout = QFormLayout(self)
        self.hours = QSpinBox()
        self.hours.setRange(0, 999)
        self.minutes = QSpinBox()
        self.minutes.setRange(0, 59)
        self.seconds = QSpinBox()
        self.seconds.setRange(0, 59)
        self.minutes.setValue(5)
        layout.addRow("Hours", self.hours)
        layout.addRow("Minutes", self.minutes)
        layout.addRow("Seconds", self.seconds)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def duration_seconds(self) -> int:
        return self.hours.value() * 3600 + self.minutes.value() * 60 + self.seconds.value()

    def accept(self) -> None:
        if self.duration_seconds() > 0:
            super().accept()


class GraphPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 6, 0, 0)
        self.plots: dict[str, pg.PlotWidget] = {}
        self.curves: dict[str, pg.PlotDataItem] = {}
        self.gpu_signature: tuple[tuple[int, str], ...] = ()
        self._build_base()

    def _new_plot(self, key: str, title: str, row: int, column: int) -> None:
        plot = pg.PlotWidget(title=title)
        plot.setBackground("#071018")
        plot.setMouseEnabled(x=False, y=False)
        plot.setMenuEnabled(False)
        plot.hideButtons()
        plot.setYRange(0, 100)
        plot.showGrid(x=False, y=True, alpha=0.15)
        plot.getAxis("bottom").setStyle(showValues=False)
        curve = plot.plot(pen=pg.mkPen("#32ddea", width=2))
        self.plots[key] = plot
        self.curves[key] = curve
        self.layout.addWidget(plot, row, column)

    def _build_base(self) -> None:
        self._new_plot("cpu", "CPU %", 0, 0)
        self._new_plot("memory", "RAM %", 0, 1)

    def ensure_gpus(self, gpus: tuple[GpuMetrics, ...]) -> None:
        signature = tuple((gpu.index, gpu.name) for gpu in gpus)
        if signature == self.gpu_signature:
            return
        for key in list(self.plots):
            if key.startswith("gpu"):
                widget = self.plots.pop(key)
                self.curves.pop(key)
                self.layout.removeWidget(widget)
                widget.deleteLater()
        for row, gpu in enumerate(gpus, start=1):
            self._new_plot(f"gpu-util-{gpu.index}", f"GPU{gpu.index} Util %", row, 0)
            self._new_plot(f"gpu-mem-{gpu.index}", f"GPU{gpu.index} Memory %", row, 1)
        self.gpu_signature = signature

    def update_history(self, history: MetricHistory) -> None:
        self.curves["cpu"].setData(list(history.cpu))
        self.curves["memory"].setData(list(history.memory))
        for index, values in history.gpu_utilization.items():
            curve = self.curves.get(f"gpu-util-{index}")
            if curve is not None:
                curve.setData(list(values))
        for index, values in history.gpu_memory.items():
            curve = self.curves.get(f"gpu-mem-{index}")
            if curve is not None:
                curve.setData(list(values))


class MainWindow(QWidget):
    def __init__(self, config_store: ConfigStore, config: AppConfig) -> None:
        super().__init__()
        self.config_store = config_store
        self.config = config
        self.timekeeper = Timekeeper()
        self.history = MetricHistory(config.history_seconds, config.refresh_interval_ms)
        self.worker: MetricsThread | None = None
        self._quitting = False
        self._gpu_signature: tuple[tuple[int, str], ...] | None = None
        self._font_shortcuts: list[QShortcut] = []

        flags = Qt.FramelessWindowHint | Qt.Tool
        if config.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setObjectName("hud")
        self.setMinimumSize(300, 180)
        self.resize(config.window_width, config.window_height)
        self.setStyleSheet(build_stylesheet(config.font_scale_percent))
        self.setWindowTitle("SysScope")
        self.setWindowIcon(make_icon())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._build_ui()
        self._build_shortcuts()
        self._build_tray()
        self._set_compact(config.compact_mode, persist=False)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_time_display)
        self.clock_timer.start(33)
        self._update_time_display()
        self.switch_source(config.metrics_source, persist=False)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(7)

        header = QHBoxLayout()
        time_box = QVBoxLayout()
        self.time_label = QLabel()
        self.time_label.setObjectName("timeDisplay")
        self.source_label = QLabel("SOURCE: STARTING")
        self.source_label.setObjectName("sourceLabel")
        time_box.addWidget(self.time_label)
        time_box.addWidget(self.source_label)
        header.addLayout(time_box, 1)

        self.menu_button = QPushButton("Menu")
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setToolTip("Open SysScope menu")
        self.menu_button.clicked.connect(self._show_menu_from_button)
        header.addWidget(self.menu_button, 0, Qt.AlignTop)

        self.session_controls = QWidget()
        controls = QHBoxLayout(self.session_controls)
        controls.setContentsMargins(0, 0, 0, 0)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._reset_session)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.reset_button)
        self.session_controls.hide()
        header.addWidget(self.session_controls)
        root.addLayout(header)

        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(6)
        self.cpu_card = MetricCard("CPU")
        self.memory_card = MetricCard("RAM")
        self.cards_layout.addWidget(self.cpu_card, 0, 0)
        self.cards_layout.addWidget(self.memory_card, 0, 1)
        root.addLayout(self.cards_layout)

        self.gpu_cards: dict[int, MetricCard] = {}

        self.expanded_panel = QWidget()
        expanded_layout = QVBoxLayout(self.expanded_panel)
        expanded_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_panel = GraphPanel()
        expanded_layout.addWidget(self.graph_panel, 1)
        footer = QHBoxLayout()
        self.gc_button = QPushButton("GC")
        self.gc_button.clicked.connect(self._run_gc)
        self.gc_result = QLabel("GC ready")
        self.gc_result.setObjectName("statusLabel")
        footer.addWidget(self.gc_button)
        footer.addWidget(self.gc_result)
        footer.addStretch()
        expanded_layout.addLayout(footer)
        root.addWidget(self.expanded_panel, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("SysScope")
        menu = QMenu()
        show_action = menu.addAction("Show SysScope")
        show_action.triggered.connect(self._show_from_tray)
        hide_action = menu.addAction("Hide SysScope")
        hide_action.triggered.connect(self.hide)
        menu.addSeparator()
        exit_action = menu.addAction("Exit SysScope")
        exit_action.triggered.connect(self.exit_application)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_from_tray()

    def _show_context_menu(self, position: QPoint) -> None:
        self._create_menu().exec(self.mapToGlobal(position))

    def _show_menu_from_button(self) -> None:
        menu = self._create_menu()
        menu.exec(self.menu_button.mapToGlobal(QPoint(0, self.menu_button.height())))

    def _create_menu(self) -> QMenu:
        menu = QMenu(self)
        display_menu = menu.addMenu("Display")
        display_group = QActionGroup(display_menu)
        compact_action = display_menu.addAction("Compact")
        compact_action.setCheckable(True)
        compact_action.setChecked(self.config.compact_mode)
        compact_action.triggered.connect(lambda: self._set_compact(True))
        display_group.addAction(compact_action)
        expanded_action = display_menu.addAction("Expanded")
        expanded_action.setCheckable(True)
        expanded_action.setChecked(not self.config.compact_mode)
        expanded_action.triggered.connect(lambda: self._set_compact(False))
        display_group.addAction(expanded_action)

        time_menu = menu.addMenu("Timekeeping")
        start_stopwatch = time_menu.addAction("Start Stopwatch")
        start_stopwatch.triggered.connect(self._start_stopwatch)
        start_timer = time_menu.addAction("Start Timer")
        start_timer.triggered.connect(self._start_timer)
        if self.timekeeper.active:
            time_menu.addSeparator()
            pause_label = "Resume" if self.timekeeper.paused else "Pause"
            pause_action = time_menu.addAction(pause_label)
            pause_action.setEnabled(not self.timekeeper.finished)
            pause_action.triggered.connect(self._toggle_pause)
            reset_action = time_menu.addAction("Reset")
            reset_action.triggered.connect(self._reset_session)

        source_menu = menu.addMenu("Metrics Source")
        source_group = QActionGroup(source_menu)
        source_group.setExclusive(True)
        self._add_source_action(source_menu, source_group, "host", "Local Host")
        if platform.system() == "Windows":
            for distribution in discover_wsl_distributions():
                self._add_source_action(
                    source_menu,
                    source_group,
                    f"wsl:{distribution}",
                    f"WSL: {distribution}",
                )

        zoom_menu = menu.addMenu("Font Size")
        zoom_in_action = zoom_menu.addAction("Increase  Ctrl++")
        zoom_in_action.setEnabled(self.config.font_scale_percent < MAX_FONT_SCALE)
        zoom_in_action.triggered.connect(self._increase_font_scale)
        zoom_out_action = zoom_menu.addAction("Decrease  Ctrl+-")
        zoom_out_action.setEnabled(self.config.font_scale_percent > MIN_FONT_SCALE)
        zoom_out_action.triggered.connect(self._decrease_font_scale)
        zoom_menu.addSeparator()
        scale_action = zoom_menu.addAction(f"{self.config.font_scale_percent}%")
        scale_action.setEnabled(False)

        menu.addSeparator()
        exit_action = menu.addAction("Exit SysScope")
        exit_action.triggered.connect(self.exit_application)
        return menu

    def _build_shortcuts(self) -> None:
        for sequence in ("Ctrl++", "Ctrl+="):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self._increase_font_scale)
            self._font_shortcuts.append(shortcut)
        shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self._decrease_font_scale)
        self._font_shortcuts.append(shortcut)

    def _increase_font_scale(self) -> None:
        self._set_font_scale(self.config.font_scale_percent + FONT_SCALE_STEP)

    def _decrease_font_scale(self) -> None:
        self._set_font_scale(self.config.font_scale_percent - FONT_SCALE_STEP)

    def _set_font_scale(self, scale_percent: int, persist: bool = True) -> None:
        bounded = max(MIN_FONT_SCALE, min(MAX_FONT_SCALE, scale_percent))
        if bounded == self.config.font_scale_percent:
            return
        self.config.font_scale_percent = bounded
        self.setStyleSheet(build_stylesheet(bounded))
        if persist:
            self._save_config()

    def _add_source_action(
        self, menu: QMenu, group: QActionGroup, source_id: str, label: str
    ) -> None:
        action = QAction(label, menu)
        action.setCheckable(True)
        action.setChecked(self.config.metrics_source == source_id)
        action.triggered.connect(lambda checked=False, value=source_id: self.switch_source(value))
        group.addAction(action)
        menu.addAction(action)

    def _set_compact(self, compact: bool, persist: bool = True) -> None:
        self.config.compact_mode = compact
        self.expanded_panel.setVisible(not compact)
        if compact:
            self.resize(max(340, self.width()), max(200, min(self.height(), 340)))
        else:
            self.resize(max(620, self.width()), max(560, self.height()))
        if persist:
            self._save_config()

    def switch_source(self, source_id: str, persist: bool = True) -> None:
        self._stop_worker()
        self.config.metrics_source = source_id
        self.history = MetricHistory(
            self.config.history_seconds, self.config.refresh_interval_ms
        )
        self.cpu_card.set_series(())
        self.memory_card.set_series(())
        for card in self.gpu_cards.values():
            card.set_series(())
        self.source_label.setText(f"SOURCE: {source_id.upper()}")
        self.status_label.setText("Connecting...")
        self.worker = MetricsThread(source_id, self.config.refresh_interval_ms)
        self.worker.snapshotReady.connect(self._apply_snapshot)
        self.worker.sourceError.connect(self._show_source_error)
        self.worker.fallbackRequested.connect(self._fallback_to_host)
        self.worker.start()
        if persist:
            self._save_config()

    def _stop_worker(self) -> None:
        if self.worker is None:
            return
        self.worker.request_stop()
        self.worker.wait(3000)
        self.worker = None

    def _fallback_to_host(self) -> None:
        if self.config.metrics_source != "host":
            QTimer.singleShot(0, lambda: self.switch_source("host"))

    def _show_source_error(self, message: str) -> None:
        self.status_label.setText(f"Source error: {message}")

    def _apply_snapshot(self, snapshot: MetricSnapshot) -> None:
        self.status_label.setText("")
        self.source_label.setText(f"SOURCE: {snapshot.source_id.upper()}")
        self.cpu_card.value.setText(f"{snapshot.cpu.utilization_percent:.0f}%")
        self.memory_card.value.setText(
            f"{snapshot.memory.utilization_percent:.0f}%  "
            f"{format_bytes(snapshot.memory.used_bytes)} / "
            f"{format_bytes(snapshot.memory.total_bytes)}"
        )
        self._ensure_gpu_cards(snapshot.gpus)
        for gpu in snapshot.gpus:
            temperature = "--" if gpu.temperature_c is None else f"{gpu.temperature_c:.0f} C"
            self.gpu_cards[gpu.index].value.setText(
                f"{gpu.utilization_percent:.0f}%  {temperature}  "
                f"{format_bytes(gpu.memory_used_bytes)} / "
                f"{format_bytes(gpu.memory_total_bytes)}"
            )
        self.history.append(snapshot)
        self.cpu_card.set_series(self.history.cpu)
        self.memory_card.set_series(self.history.memory)
        for gpu in snapshot.gpus:
            self.gpu_cards[gpu.index].set_series(
                self.history.gpu_utilization[gpu.index]
            )
        self.graph_panel.ensure_gpus(snapshot.gpus)
        if not self.config.compact_mode:
            self.graph_panel.update_history(self.history)

    def _ensure_gpu_cards(self, gpus: tuple[GpuMetrics, ...]) -> None:
        signature = tuple((gpu.index, gpu.name) for gpu in gpus)
        if signature == self._gpu_signature:
            return
        for card in self.gpu_cards.values():
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.gpu_cards.clear()
        if not gpus:
            card = MetricCard("GPU")
            card.value.setText("NVIDIA GPU unavailable")
            self.cards_layout.addWidget(card, 1, 0, 1, 2)
            self.gpu_cards[-1] = card
        else:
            for row, gpu in enumerate(gpus, start=1):
                card = MetricCard(f"GPU{gpu.index}  {gpu.name}")
                self.cards_layout.addWidget(card, row, 0, 1, 2)
                self.gpu_cards[gpu.index] = card
        self._gpu_signature = signature

    def _update_time_display(self) -> None:
        if self.timekeeper.active:
            self.time_label.setText(self.timekeeper.display_text())
            mode = self.timekeeper.mode.value.upper()
            if self.timekeeper.finished:
                mode += " COMPLETE"
                self.pause_button.setEnabled(False)
            elif self.timekeeper.paused:
                mode += " PAUSED"
                self.pause_button.setEnabled(True)
            else:
                self.pause_button.setEnabled(True)
            self.pause_button.setText("Resume" if self.timekeeper.paused else "Pause")
            self.source_label.setToolTip(mode)
            self.session_controls.show()
        else:
            clock_format = "%H:%M:%S" if self.config.clock_24_hour else "%I:%M:%S %p"
            self.time_label.setText(datetime.now().strftime(clock_format))
            self.session_controls.hide()

    def _start_stopwatch(self) -> None:
        self.timekeeper.start_stopwatch()
        self._update_time_display()

    def _start_timer(self) -> None:
        dialog = TimerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.timekeeper.start_timer(dialog.duration_seconds())
            self._update_time_display()

    def _toggle_pause(self) -> None:
        if self.timekeeper.paused:
            self.timekeeper.resume()
        else:
            self.timekeeper.pause()
        self._update_time_display()

    def _reset_session(self) -> None:
        self.timekeeper.reset()
        self._update_time_display()

    def _run_gc(self) -> None:
        collected = gc.collect()
        self.gc_result.setText(f"Collected {collected} objects")

    def _save_config(self) -> None:
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        try:
            self.config_store.save(self.config)
        except OSError as error:
            self.status_label.setText(f"Config could not be saved: {error}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            edges = self._resize_edges(event.position().toPoint())
            handle = self.windowHandle()
            if handle is not None and edges:
                handle.startSystemResize(edges)
                event.accept()
                return
            child = self.childAt(event.position().toPoint())
            if handle is not None and not isinstance(child, (QPushButton, QSpinBox)):
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def _resize_edges(self, point: QPoint) -> Qt.Edges:
        margin = 7
        edges = Qt.Edges()
        if point.x() <= margin:
            edges |= Qt.LeftEdge
        elif point.x() >= self.width() - margin:
            edges |= Qt.RightEdge
        if point.y() <= margin:
            edges |= Qt.TopEdge
        elif point.y() >= self.height() - margin:
            edges |= Qt.BottomEdge
        return edges

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self.config.window_width = self.width()
            self.config.window_height = self.height()

    def closeEvent(self, event) -> None:
        if self._quitting:
            event.accept()
            return
        self.hide()
        event.ignore()

    def exit_application(self) -> None:
        self._quitting = True
        self._save_config()
        self._stop_worker()
        self.tray.hide()
        QApplication.instance().quit()

