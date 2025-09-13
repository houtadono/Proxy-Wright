from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QHBoxLayout, QPushButton, QMessageBox
)
from workers.proxy_check_worker import ProxyCheckWorker


class ProxyDialog(QDialog):
    def __init__(self, parent=None, data: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Proxy"))
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["http", "https", "socks5"])
        self.host = QLineEdit()
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(8080)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        layout.addRow(self.tr("Name"), self.name)
        layout.addRow(self.tr("Type"), self.proxy_type)
        layout.addRow(self.tr("Host"), self.host)
        layout.addRow(self.tr("Port"), self.port)
        layout.addRow(self.tr("Username"), self.username)
        layout.addRow(self.tr("Password"), self.password)

        btns = QHBoxLayout()
        self.btn_test = QPushButton(self.tr("Test"))
        self.btn_ok = QPushButton(self.tr("Save"))
        self.btn_cancel = QPushButton(self.tr("Cancel"))
        btns.addWidget(self.btn_test)
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addRow(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_test.clicked.connect(self.on_test)

        if data:
            self.name.setText(data.get("name", ""))
            self.proxy_type.setCurrentText(data.get("proxy_type", "http"))
            self.host.setText(data.get("host", ""))
            self.port.setValue(int(data.get("port", 8080)))
            self.username.setText(data.get("username") or "")
            self.password.setText(data.get("password") or "")

    def payload(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "proxy_type": self.proxy_type.currentText(),
            "host": self.host.text().strip(),
            "port": int(self.port.value()),
            "username": self.username.text().strip() or None,
            "password": self.password.text() or None,
        }

    def on_test(self):
        p = self.payload()
        if not p["name"] or not p["host"]:
            QMessageBox.warning(self, self.tr("Missing Info"), self.tr("Name and Host are required."))
            return
        self.btn_test.setEnabled(False)
        self.worker = ProxyCheckWorker(p)
        self.worker.finished_ok.connect(self._ok)
        self.worker.failed.connect(self._fail)
        self.worker.start()

    def _ok(self, msg: str):
        self.btn_test.setEnabled(True)
        QMessageBox.information(self, self.tr("Proxy OK"), self.tr("Result: {0}").format(msg))

    def _fail(self, err: str):
        self.btn_test.setEnabled(True)
        QMessageBox.critical(self, self.tr("Proxy Error"), err)
