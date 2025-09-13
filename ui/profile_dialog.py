from typing import Optional
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QHBoxLayout, QPushButton


class ProfileDialog(QDialog):
    def __init__(self, parent=None, data: Optional[dict] = None, proxies: list[dict] = []):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Create Profile"))
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.proxy_select = QComboBox()
        self.proxy_select.addItem(self.tr("(None)"), userData=None)
        for pr in proxies:
            label = f"[{pr['id']}] {pr['name']} — {pr['proxy_type']}://{pr['host']}:{pr['port']}" + (
                " (auth)" if pr.get('username') else "")
            self.proxy_select.addItem(label, userData=pr['id'])

        layout.addRow(self.tr("Name"), self.name)
        layout.addRow(self.tr("Proxy"), self.proxy_select)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton(self.tr("Save"))
        self.btn_cancel = QPushButton(self.tr("Cancel"))
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addRow(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)

        self.data = data or {}
        if data:
            self.name.setText(data.get("name", ""))
            # chọn proxy_id nếu có
            pid = data.get("proxy_id")
            if pid is not None:
                idx = self.proxy_select.findData(pid)
                if idx >= 0: self.proxy_select.setCurrentIndex(idx)

    def get_payload(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "proxy_id": self.proxy_select.currentData(),
        }
