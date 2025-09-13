import os
import subprocess
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QFrame, QSizePolicy, QComboBox, QProgressDialog
)

from config import APP_VERSION
from core.paths import BROWSERS_DIR
from core.settings import AppSettings
from core.updater import UpdaterService
from services.playwright_service import PlaywrightManager
from ui.install_dialog import InstallDialog
from workers.update_worker import CheckUpdateWorker, DownloadInstallWorker


class SettingTab(QWidget):
    """
    Single Settings tab:
      - App info + 'Check for Updates'
      - Playwright browsers status + Install/Update + Refresh + Open Folder
      - Language select
    """
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.manager = PlaywrightManager()
        self._saved_lang = self.settings.get_lang()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # ---------- Application ----------
        app_group = QGroupBox(self.tr("Application"))
        app_layout = QHBoxLayout(app_group)
        app_layout.setContentsMargins(12, 8, 12, 8)

        self.app_label = QLabel(self.tr("Current version: {0}").format(APP_VERSION))
        self.app_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.btn_check_app = QPushButton("🔎 " + self.tr("Check for Updates"))
        self.btn_check_app.setToolTip(self.tr("Fetch latest version and release notes."))
        self.btn_check_app.clicked.connect(self.on_check_app_update)

        app_layout.addWidget(self.app_label)
        app_layout.addStretch()
        app_layout.addWidget(self.btn_check_app)
        root.addWidget(app_group)
        self.updater = UpdaterService()
        # UI helpers
        self._check_worker = None
        self._dl_worker = None
        self._progress = None

        # ---------- Playwright ----------
        pw_group = QGroupBox(self.tr("Playwright Browser"))
        pw_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        pw_layout = QVBoxLayout(pw_group)
        pw_layout.setContentsMargins(12, 8, 12, 8)
        pw_layout.setSpacing(8)

        # Banner nếu chưa có browser
        self.banner = QFrame()
        self.banner.setObjectName("browserBanner")
        self.banner.setStyleSheet("""
            QFrame#browserBanner {
                background: #2d323a; border: 1px solid #3d434c; border-radius: 10px;
            }
            QFrame#browserBanner QLabel { color: #e6e6e6; }
        """)
        banner_row = QHBoxLayout(self.banner)
        banner_row.setContentsMargins(12, 10, 12, 10)
        icon = QLabel("⚠️"); icon.setAlignment(Qt.AlignTop)
        text = QLabel(self.tr("No Playwright browser detected. Click Install to download Chromium."))
        text.setWordWrap(True)
        banner_row.addWidget(icon)
        banner_row.addWidget(text, 1)
        pw_layout.addWidget(self.banner)

        # Khu nội dung: Bảng (trái) + Cột nút (phải)
        content_row = QHBoxLayout()
        content_row.setSpacing(10)

        # Bảng phiên bản
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([self.tr("Browser"), self.tr("Version")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        content_row.addWidget(self.table, 1)  # stretch 1 cho bảng

        # Cột nút bên phải (dọc)
        side_widget = QWidget()
        side_layout = QVBoxLayout(side_widget)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)

        self.btn_install = QPushButton()
        self.btn_install.setToolTip(self.tr("Download Chromium via Playwright to the app data folder."))
        self.btn_install.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_install.clicked.connect(self.on_install_clicked)

        self.btn_refresh = QPushButton(self.tr("Refresh"))
        self.btn_refresh.setToolTip(self.tr("Rescan installed Playwright browsers."))
        self.btn_refresh.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_refresh.clicked.connect(self.on_refresh_clicked)

        self.btn_open_dir = QPushButton("📂 " + self.tr("Open Folder"))
        self.btn_open_dir.setToolTip(str(BROWSERS_DIR))
        self.btn_open_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_open_dir.clicked.connect(self.on_open_dir)

        side_widget.setFixedWidth(180)
        side_layout.addWidget(self.btn_install)
        side_layout.addWidget(self.btn_refresh)
        side_layout.addWidget(self.btn_open_dir)
        side_layout.addStretch()

        content_row.addWidget(side_widget, 0)
        pw_layout.addLayout(content_row)
        root.addWidget(pw_group)

        # ---------- Language ----------
        lang_group = QGroupBox(self.tr("Language"))
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.setContentsMargins(12, 8, 12, 8)
        lang_layout.setSpacing(8)

        lang_label = QLabel(self.tr("Choose Language:"))

        self.lang_combo = QComboBox()
        self.lang_combo.addItem(self.tr("English"), "en")
        self.lang_combo.addItem(self.tr("Vietnamese"), "vi")
        self.lang_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lang_combo.setMinimumWidth(220)

        # set giá trị đã lưu
        idx = self.lang_combo.findData(self._saved_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        self.btn_save_lang = QPushButton(self.tr("💾 Save"))
        self.btn_save_lang.clicked.connect(self.on_save_lang)
        self.btn_save_lang.setVisible(False)  # ẩn mặc định

        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)

        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo, 1)
        lang_layout.addWidget(self.btn_save_lang)
        root.addWidget(lang_group)

        root.addStretch()

        # First refresh after the UI shows
        QTimer.singleShot(0, self.post_init)

    # ---------- Lifecycle ----------
    def post_init(self):
        self.refresh_table()
        self.refresh_install_button()
        self.update_banner_visibility()

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh_table()
        self.refresh_install_button()
        self.update_banner_visibility()

    # ---------- Helpers ----------
    def refresh_table(self):
        versions = self.manager.get_installed_versions()
        rows = sorted(versions.items())
        self.table.setRowCount(len(rows))
        for r, (name, rev) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(str(rev)))

    def refresh_install_button(self):
        has = self.manager.is_installed("chromium")
        self.btn_install.setText(self.tr("Update (Chromium)") if has else "⬇️ " + self.tr("Install (Chromium)"))
        self.btn_install.setEnabled(True)

    def update_banner_visibility(self):
        self.banner.setVisible(self.table.rowCount() == 0)

    # ---------- Actions ----------
    def on_check_app_update(self):
        self.btn_check_app.setEnabled(False)

        # Small "checking..." progress
        checking = QProgressDialog(self.tr("Checking for updates..."), self.tr("Cancel"), 0, 0, self)
        checking.setWindowModality(Qt.WindowModal)
        checking.setMinimumDuration(0)
        checking.setAutoClose(True)
        checking.show()

        self._check_worker = CheckUpdateWorker(self.updater, accept_prerelease=False)
        self._check_worker.finishedResult.connect(lambda info, err: self._on_check_finished(info, err, checking))
        self._check_worker.finished.connect(lambda: self.btn_check_app.setEnabled(True))
        self._check_worker.start()

    def _on_check_finished(self, info, error, checking_dialog):
        checking_dialog.cancel()
        if error:
            QMessageBox.critical(self, self.tr("Update"), self.tr("Failed to check updates:\n{0}").format(error))
            return

        if not info:
            QMessageBox.information(
                self,
                self.tr("Update"),
                self.tr("You're on the latest version.\nCurrent: v{0}").format(APP_VERSION),
            )
            return

        # Có bản mới -> hiển thị notes + hỏi cập nhật
        msg = QMessageBox(self)
        msg.setWindowTitle(self.tr("New version available"))
        msg.setIcon(QMessageBox.Information)
        msg.setText(self.tr("Current: v{0}\nLatest: {1}").format(APP_VERSION, info.tag))
        # Dùng detailedText để show notes (plain)
        if info.notes:
            msg.setDetailedText(info.notes)
        btn_update = msg.addButton(self.tr("Download && Install"), QMessageBox.AcceptRole)
        btn_view = msg.addButton(self.tr("View on GitHub"), QMessageBox.ActionRole)
        msg.addButton(self.tr("Later"), QMessageBox.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_view:
            import webbrowser
            url = self.updater.repo_web_url or "https://github.com"
            webbrowser.open(url)
            return
        if clicked != btn_update:
            return

        # Bắt đầu tải & cài
        self._progress = QProgressDialog(self.tr("Downloading..."), self.tr("Cancel"), 0, 100, self)
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setValue(0)
        self._progress.show()

        self._dl_worker = DownloadInstallWorker(self.updater, info)
        self._dl_worker.progress.connect(self._on_dl_progress)
        self._dl_worker.failed.connect(self._on_dl_failed)
        self._dl_worker.startedInstalling.connect(self._on_started_installing)
        self._dl_worker.start()

    def _on_dl_progress(self, done: int, total: int):
        if not self._progress or total <= 0:
            return
        pct = int(done * 100 / total)
        self._progress.setValue(min(99, pct))

    def _on_dl_failed(self, err: str):
        if self._progress:
            self._progress.cancel()
        QMessageBox.critical(self, self.tr("Update"), self.tr("Download failed:\n{0}").format(err))

    def _on_started_installing(self):
        # Bước này service sẽ spawn installer/updater rồi THOÁT app.
        if self._progress:
            self._progress.setLabelText(self.tr("Installing..."))
            self._progress.setValue(100)

    def on_open_dir(self):
        path = str(BROWSERS_DIR)
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def on_install_clicked(self):
        dlg = InstallDialog(self.manager, self, browser="chromium")
        dlg.finished.connect(lambda _: (
            self.refresh_table(),
            self.refresh_install_button(),
            self.update_banner_visibility()
        ))
        dlg.show()

    def on_refresh_clicked(self):
        self.refresh_table()
        self.refresh_install_button()
        self.update_banner_visibility()

    def on_lang_changed(self, _index: int):
        code = self.lang_combo.currentData()
        self.btn_save_lang.setVisible(code != self._saved_lang)

    def on_save_lang(self):
        code = self.lang_combo.currentData()
        self.settings.set_lang(code)
        self._saved_lang = code
        self.btn_save_lang.setVisible(False)  # ẩn lại sau khi lưu

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(self.tr("Language Saved"))
        msg.setText(self.tr("You need to restart the application to apply the new language."))
        restart_btn = msg.addButton(self.tr("Restart Now"), QMessageBox.AcceptRole)
        msg.addButton(self.tr("Later"), QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == restart_btn:
            python = sys.executable
            os.execl(python, python, *sys.argv)
