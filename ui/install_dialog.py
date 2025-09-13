# ui/install_dialog.py
from __future__ import annotations
from PySide6.QtCore import QThread, Signal, QObject, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QDialogButtonBox
)

class _InstallWorker(QObject):
    """Emit structured events from PlaywrightManager.install_browser_events()."""
    event = Signal(object)  # ("progress", pct, total) | ("line", text) | ("done", ok)

    def __init__(self, manager, browser: str = "chromium"):
        super().__init__()
        self.manager = manager
        self.browser = browser

    def run(self):
        try:
            for ev in self.manager.install_browser_events(self.browser):
                self.event.emit(ev)
        except Exception as e:
            self.event.emit(("line", f"[ERROR] {e}"))
            self.event.emit(("done", False))


class InstallDialog(QDialog):
    """
    Minimal install dialog:
      - Live logs
      - 'Run in Background' hides the dialog; once finished, it shows again
      - On success, hide the 'Run in Background' button
    """
    def __init__(self, manager, parent=None, browser: str = "chromium"):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Install Playwright Browser"))
        self.resize(720, 420)
        self.setModal(True)

        self._manager = manager
        self._browser = browser
        self._backgrounded = False

        root = QVBoxLayout(self)

        # Header + status line
        self.title = QLabel(self.tr("Installing <b>{}</b>…").format(browser.capitalize()))
        self.title.setTextFormat(Qt.RichText)
        self.status = QLabel(self.tr("Starting…"))
        root.addWidget(self.title)
        root.addWidget(self.status)

        # Log area
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(self.tr("Logs will appear here…"))
        self.log.setMinimumHeight(260)
        root.addWidget(self.log, 1)

        # Buttons
        btns = QDialogButtonBox()
        self.btn_bg = QPushButton(self.tr("Run in Background"))
        self.btn_close = QPushButton(self.tr("Close"))
        self.btn_close.setEnabled(False)  # enabled when finished
        btns.addButton(self.btn_bg, QDialogButtonBox.ActionRole)
        btns.addButton(self.btn_close, QDialogButtonBox.AcceptRole)
        root.addWidget(btns)

        self.btn_bg.clicked.connect(self._on_background)
        self.btn_close.clicked.connect(self.accept)

        # Worker thread
        self._t = QThread(self)
        self._w = _InstallWorker(self._manager, browser=self._browser)
        self._w.moveToThread(self._t)
        self._t.started.connect(self._w.run)
        self._w.event.connect(self._on_event)
        self._t.finished.connect(self._t.deleteLater)
        self._t.start()

    # ----------------------------
    # Events from worker
    # ----------------------------
    def _on_event(self, ev):
        kind = ev[0]
        if kind == "line":
            _, text = ev
            self.log.appendPlainText(text)
            # simple status heuristics
            if "Downloading" in text:
                self.status.setText(self.tr("Downloading…"))
            elif "extract" in text.lower():
                self.status.setText(self.tr("Extracting…"))
            return

        if kind == "done":
            _, ok = ev
            # Bring dialog back if it was hidden
            if self._backgrounded or not self.isVisible():
                self.show()
                try:
                    self.raise_()
                    self.activateWindow()
                except Exception:
                    pass

            self.btn_close.setEnabled(True)
            self.btn_bg.setEnabled(False)
            if ok:
                self.status.setText(self.tr("Completed."))
                self.log.appendPlainText("[OK] Browser installed.")
            else:
                self.status.setText(self.tr("Failed. See logs above."))
            self._t.quit()

    # ----------------------------
    # UI handlers
    # ----------------------------
    def _on_background(self):
        """Hide dialog; installation continues in background."""
        self._backgrounded = True
        self.hide()
