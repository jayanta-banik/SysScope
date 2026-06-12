from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from sysscope.config import ConfigStore
from sysscope.ui.main_window import MainWindow


def main() -> int:
    QCoreApplication.setApplicationName("SysScope")
    QCoreApplication.setOrganizationName("SysScope")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    store = ConfigStore()
    config = store.load()
    window = MainWindow(store, config)
    app.aboutToQuit.connect(window._stop_worker)
    if not config.start_minimized:
        window.show()
    return app.exec()

