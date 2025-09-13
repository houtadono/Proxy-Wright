from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout
)

from config import APP_VERSION
from services.playwright_service import PlaywrightManager
from services.update_service import check_app_update
from ui.update_dialog import UpdateDialog
import sys, os

from utils.path_helper import get_app_dir


class UpdateTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # --- App Info ---
        app_group = QGroupBox("Ứng dụng")
        app_layout = QHBoxLayout(app_group)
        self.app_label = QLabel(f"Phiên bản hiện tại: {APP_VERSION}")
        app_layout.addWidget(self.app_label)

        self.btn_check_app = QPushButton("🔎 Kiểm tra cập nhật")
        self.btn_check_app.clicked.connect(self.on_check_app_update)
        app_layout.addWidget(self.btn_check_app)
        layout.addWidget(app_group)

        # --- Browsers Info (chỉ xem, không update) ---
        pw_group = QGroupBox("Trình duyệt Playwright (đi kèm)")
        pw_layout = QVBoxLayout(pw_group)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Browser", "Phiên bản"])
        self.table.horizontalHeader().setStretchLastSection(True)
        pw_layout.addWidget(self.table)

        layout.addWidget(pw_group)
        layout.addStretch()

        # Manager
        app_dir = get_app_dir()
        self.manager = PlaywrightManager(app_dir)

        # Load
        self.refresh_table()

    def refresh_table(self):
        versions = self.manager.get_installed_versions()
        self.table.setRowCount(0)
        for name, ver in versions.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(ver)))

    def on_check_app_update(self):
        has_update, current, latest, updates = check_app_update()
        self.app_label.setText(f"Phiên bản hiện tại: {current}")

        if not latest:
            QMessageBox.warning(self, "Lỗi", "Không kiểm tra được phiên bản mới.")
            return

        if has_update:
            dlg = UpdateDialog(current, updates, self)
            dlg.exec()
        else:
            QMessageBox.information(self, "Thông báo", f"Bạn đang dùng bản mới nhất ({current}).")
