import json
import os
import shutil

import psutil
from PySide6.QtCore import Qt, QCoreApplication, QThread, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QMessageBox, QTabWidget, QFileDialog, QToolButton, QComboBox,
    QHeaderView
)

from repo import (
    list_profiles, get_profile, create_profile, update_profile, delete_profile, get_proxy,
    delete_proxy, list_proxies, create_proxy, update_proxy
)
from ui.profile_dialog import ProfileDialog
from ui.proxy_dialog import ProxyDialog
from ui.update_tab import UpdateTab
from workers.browser_worker import BrowserWorker, profile_data_dir


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy Profile Manager (Python)")
        self.resize(1000, 620)
        self._apply_qss()

        v = QVBoxLayout(self)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs)

        # ---- Tab Profiles ----
        self._init_profiles_tab()

        # ---- Tab Proxies ----
        self._init_proxies_tab()

        # ---- Tab Update ----
        self.tabs.addTab(UpdateTab(), "Cập nhật")

        self.workers: dict[int, BrowserWorker] = {}
        self.refresh_profiles()
        self.refresh_proxies()

    # ========== UI Builders ==========
    def _apply_qss(self):
        self.setStyleSheet("""
        QWidget { background:#1e1f22; color:#eaeaea; font-size:13px; }

        QTableWidget {
            gridline-color:#2a2c31; alternate-background-color:#212329;
        }
        /* Quan trọng: tự set màu khi hàng/cell được chọn */
        QTableWidget::item:selected { background:#2f3238; color:#ffffff; }

        QHeaderView::section {
            background:#22242a; padding:6px; border:0; border-right:1px solid #2a2c31;
        }

        QPushButton, QToolButton { background:#2f3238; border:1px solid #3b3e45; padding:4px 8px; border-radius:8px; }
        QPushButton:hover, QToolButton:hover { background:#3a3d44; }
        QPushButton:disabled, QToolButton:disabled { color:#9aa0a6; }

        /* ComboBox hiển thị */
        QComboBox {
            background:#23252b; color:#eaeaea; border:1px solid #343844; border-radius:6px; padding:5px 8px;
        }
        QComboBox:hover, QComboBox:focus { background:#2f3238; border:1px solid #4a90e2; color:#ffffff; }

        /* Danh sách thả xuống */
        QComboBox QAbstractItemView {
            background:#1e1f22; color:#eaeaea;
            selection-background-color:#17601b; selection-color:#ffffff;
            outline:0;
        }

        QToolButton[variant="success"] { background:#134e16; border:1px solid #1e7a23; }
        QToolButton[variant="success"]:hover { background:#17601b; }
        QToolButton[variant="danger"]  { background:#6b1111; border:1px solid #a11b1b; }
        QToolButton[variant="danger"]:hover  { background:#7f1515; }
        """)

    def _init_profiles_tab(self):
        self.tab_profiles = QWidget()
        self.tabs.addTab(self.tab_profiles, "Profiles")
        vp = QVBoxLayout(self.tab_profiles)

        bar = QHBoxLayout()
        self.btn_p_add = QPushButton("➕ Thêm profile")
        self.btn_p_export = QPushButton("⬇️ Export JSON")
        self.btn_p_import = QPushButton("⬆️ Import JSON")
        bar.addWidget(self.btn_p_add)
        bar.addStretch(1)
        bar.addWidget(self.btn_p_import)
        bar.addWidget(self.btn_p_export)
        vp.addLayout(bar)

        self.tbl_profiles = QTableWidget(0, 4)
        self.tbl_profiles.setHorizontalHeaderLabels(["ID", "Tên", "Proxy", "Hành động"])
        self.tbl_profiles.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_profiles.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_profiles.setSortingEnabled(True)
        vp.addWidget(self.tbl_profiles)

        self.btn_p_add.clicked.connect(self.on_profile_add)
        self.btn_p_export.clicked.connect(self.on_profile_export)
        self.btn_p_import.clicked.connect(self.on_profile_import)

    def _init_proxies_tab(self):
        self.tab_proxies = QWidget()
        self.tabs.addTab(self.tab_proxies, "Proxies")
        vq = QVBoxLayout(self.tab_proxies)

        bar = QHBoxLayout()
        self.btn_q_add = QPushButton("➕ Thêm proxy")
        self.btn_q_export = QPushButton("⬇️ Export JSON")
        self.btn_q_import = QPushButton("⬆️ Import JSON")
        bar.addWidget(self.btn_q_add)
        bar.addStretch(1)
        bar.addWidget(self.btn_q_import)
        bar.addWidget(self.btn_q_export)
        vq.addLayout(bar)

        self.tbl_proxies = QTableWidget(0, 6)
        self.tbl_proxies.setHorizontalHeaderLabels(["ID", "Tên", "Loại", "Host:Port", "Auth", "Hành động"])
        self.tbl_proxies.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_proxies.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_proxies.setSortingEnabled(True)
        vq.addWidget(self.tbl_proxies)

        self.btn_q_add.clicked.connect(self.on_proxy_add)
        self.btn_q_export.clicked.connect(self.on_proxy_export)
        self.btn_q_import.clicked.connect(self.on_proxy_import)

    # ========== Profiles ==========
    def refresh_profiles(self):
        rows = list_profiles()
        proxies = list_proxies()  # cache 1 lần
        self.tbl_profiles.setRowCount(0)
        for r in rows:
            self._add_profile_row(r, proxies)
        self.tbl_profiles.resizeColumnsToContents()
        self.tbl_profiles.setAlternatingRowColors(True)
        self.tbl_profiles.setWordWrap(True)
        self.tbl_profiles.setTextElideMode(Qt.ElideNone)
        self.tbl_profiles.verticalHeader().setVisible(False)
        self.tbl_profiles.verticalHeader().setDefaultSectionSize(44)
        self.tbl_profiles.horizontalHeader().setStretchLastSection(False)
        hh = self.tbl_profiles.horizontalHeader()
        hh.setSectionsClickable(True)
        hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        hh.setSectionResizeMode(1, QHeaderView.Stretch)  # Tên (giãn)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)  # Proxy (giãn)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Hành động
        # self.tbl_profiles.setColumnWidth(3, 220)

    def _add_profile_row(self, prof: dict, proxies: list[dict]):
        row_idx = self.tbl_profiles.rowCount()
        self.tbl_profiles.insertRow(row_idx)

        # ID & Name
        it_id = QTableWidgetItem()
        it_id.setData(Qt.DisplayRole, int(prof["id"]))  # sort số
        self.tbl_profiles.setItem(row_idx, 0, it_id)
        self.tbl_profiles.setItem(row_idx, 1, QTableWidgetItem(prof["name"]))

        # Proxy dropdown
        dd = QComboBox()
        dd.setAttribute(Qt.WA_StyledBackground, True)
        dd.setAutoFillBackground(True)
        dd.addItem("(Không)", userData=None)
        for pr in proxies:
            dd.addItem(f"[{pr['id']}] {pr['name']} — {pr['proxy_type']}://{pr['host']}:{pr['port']}", userData=pr["id"])
        if prof.get("proxy_id") is not None:
            idx = dd.findData(prof["proxy_id"])
            if idx >= 0:
                dd.setCurrentIndex(idx)
        dd.currentIndexChanged.connect(lambda _, pid=prof["id"], combo=dd: self.on_profile_proxy_changed(pid, combo))
        self.tbl_profiles.setCellWidget(row_idx, 2, dd)

        # Hành động
        cell = QWidget()
        h = QHBoxLayout(cell)
        h.setContentsMargins(0, 0, 0, 0)
        b_toggle = QToolButton()
        b_toggle.setProperty("pid", prof["id"])
        b_toggle.setFixedWidth(60)
        self._style_toggle_btn(b_toggle, running=False)
        b_edit = QToolButton()
        b_edit.setText("Sửa")
        b_edit.setProperty("pid", prof["id"])
        b_del = QToolButton()
        b_del.setText("Xoá")
        b_del.setProperty("pid", prof["id"])
        for b in (b_toggle, b_edit, b_del): h.addWidget(b)
        h.addStretch(1)
        self.tbl_profiles.setCellWidget(row_idx, 3, cell)

        b_toggle.clicked.connect(self.on_profile_toggle)
        b_edit.clicked.connect(self.on_profile_edit)
        b_del.clicked.connect(self.on_profile_delete)

    def on_profile_proxy_changed(self, pid: int, combo: QComboBox):
        if pid in self.workers:
            # revert selection
            row = get_profile(pid)
            cur = combo.currentIndex()
            prev_idx = combo.findData(row.get("proxy_id"))
            if prev_idx >= 0:
                combo.blockSignals(True)
                combo.setCurrentIndex(prev_idx)
                combo.blockSignals(False)
            QMessageBox.information(self, "Đang chạy", "Đang mở profile, không thể đổi Proxy.")
            return
        row = get_profile(pid)
        if not row: return
        update_profile(pid, {"name": row["name"], "proxy_id": combo.currentData()})

    def _find_row_by_pid(self, pid: int) -> int:
        for r in range(self.tbl_profiles.rowCount()):
            it = self.tbl_profiles.item(r, 0)
            if not it:
                continue
            val = it.data(Qt.DisplayRole)
            if val is None:
                val = it.text()
            try:
                if int(val) == int(pid):
                    return r
            except Exception:
                pass
        return -1

    def _toggle_run_buttons(self, pid: int, running: bool):
        r = self._find_row_by_pid(pid)
        if r < 0: return
        cell = self.tbl_profiles.cellWidget(r, 3)
        if cell:
            for b in cell.findChildren(QToolButton):
                if b.property("pid") == pid:
                    if b.objectName() == "toggleBtn" or b.text() in ("Mở", "Đóng"):
                        self._style_toggle_btn(b, running)
                    elif b.text() in ("Sửa",):
                        b.setEnabled(not running)
                    elif b.text() in ("Xoá",):
                        b.setEnabled(not running)

        combo = self.tbl_profiles.cellWidget(r, 2)
        if combo and isinstance(combo, QComboBox):
            combo.setEnabled(not running)

    def on_profile_add(self):
        proxies = list_proxies()
        dlg = ProfileDialog(self, proxies=proxies)
        if dlg.exec():
            payload = dlg.get_payload()
            if not payload["name"]:
                QMessageBox.warning(self, "Thiếu thông tin", "Tên là bắt buộc.")
                return
            create_profile(payload)
            self.refresh_profiles()

    def on_profile_edit(self):
        pid = self.sender().property("pid")
        row = get_profile(pid)
        if not row:
            QMessageBox.warning(self, "Lỗi", "Profile không tồn tại.")
            return
        proxies = list_proxies()
        dlg = ProfileDialog(self, data=row, proxies=proxies)
        if dlg.exec():
            update_profile(pid, dlg.get_payload())
            self.refresh_profiles()

    def on_profile_delete(self):
        pid = self.sender().property("pid")
        if QMessageBox.question(self, "Xác nhận", "Xóa profile này?") == QMessageBox.Yes:
            delete_profile(pid)
            try:
                dir_path = profile_data_dir(pid)
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không xóa được thư mục: {e}")
            self.refresh_profiles()

    def on_profile_run(self, pid: int | None = None):
        if pid is None:
            pid = self.sender().property("pid")
        prof = get_profile(pid)
        proxy = get_proxy(prof["proxy_id"]) if prof and prof.get("proxy_id") else None

        w = BrowserWorker(profile_id=pid, proxy=proxy)
        self.workers[pid] = w
        self._toggle_run_buttons(pid, True)

        w.finished_ok.connect(lambda _: self._on_profile_finished(pid))
        w.failed.connect(lambda msg: self._on_profile_failed(pid, msg))
        w.start()

    def _on_profile_finished(self, pid: int):
        self.workers.pop(pid, None)
        self._toggle_run_buttons(pid, False)

    def _on_profile_failed(self, pid: int, msg: str):
        self.workers.pop(pid, None)
        self._toggle_run_buttons(pid, False)
        QMessageBox.critical(self, "Lỗi mở trình duyệt", msg)

    def on_profile_stop(self, pid: int | None = None):
        if pid is None:
            pid = self.sender().property("pid")

        w = self.workers.get(pid)
        if w:
            try:
                w.stop()
                QCoreApplication.processEvents()
                QThread.msleep(100)

                def _force():
                    w2 = self.workers.get(pid)
                    if w2 and hasattr(w2, "force_kill"):
                        w2.force_kill()

                QTimer.singleShot(2000, _force)
                return
            except Exception:
                pass
        self._toggle_run_buttons(pid, False)

    def _kill_profile_processes(self, pid: int):
        try:
            import os, re
            from appdirs import user_data_dir
            from config import APP_NAME, ORG_NAME
            target = os.path.abspath(os.path.join(user_data_dir(APP_NAME, ORG_NAME), "profiles", str(pid)))
            target_norm = os.path.normcase(os.path.normpath(target))
            for p in psutil.process_iter(["name", "cmdline"]):
                try:
                    nm = (p.info["name"] or "").lower()
                    if not any(k in nm for k in ("chrome", "chromium", "msedge")):
                        continue
                    cmd = p.info["cmdline"] or []
                    joined = " ".join(cmd)
                    m = re.search(r'--user-data-dir(?:=|\s+)(?:"([^"]+)"|(\S+))', joined, re.I)
                    if not m:
                        continue
                    proc_dir = m.group(1) or m.group(2)
                    proc_norm = os.path.normcase(os.path.normpath(os.path.abspath(proc_dir)))
                    if proc_norm == target_norm:
                        p.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            QMessageBox.warning(self, "Dừng thất bại", str(e))

    def on_profile_toggle(self):
        pid = self.sender().property("pid")

        running = pid in self.workers
        if running:
            self.on_profile_stop(pid)
        else:
            self.on_profile_run(pid)

    def _style_toggle_btn(self, btn: QToolButton, running: bool):
        btn.setObjectName("toggleBtn")
        btn.setText("Đóng" if running else "Mở")
        btn.setProperty("variant", "danger" if running else "success")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def on_profile_export(self):
        rows = list_profiles()
        path, _ = QFileDialog.getSaveFileName(self, "Export profiles", "profiles.json", "JSON (*.json)")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "OK", f"Đã export {len(rows)} profiles.")

    def on_profile_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import profiles", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
            cnt = 0
            for it in items:
                payload = {"name": (it.get("name") or "").strip(), "proxy_id": it.get("proxy_id")}
                if payload["name"]:
                    create_profile(payload);
                    cnt += 1
            self.refresh_profiles()
            QMessageBox.information(self, "OK", f"Đã import {cnt} profiles.")
        except Exception as e:
            QMessageBox.critical(self, "Import lỗi", str(e))

    # ========== Proxies ==========
    def refresh_proxies(self):
        rows = list_proxies()
        self.tbl_proxies.setRowCount(0)
        for r in rows:
            i = self.tbl_proxies.rowCount()
            self.tbl_proxies.insertRow(i)
            self.tbl_proxies.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.tbl_proxies.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.tbl_proxies.setItem(i, 2, QTableWidgetItem(r["proxy_type"]))
            self.tbl_proxies.setItem(i, 3, QTableWidgetItem(f"{r['host']}:{r['port']}"))
            self.tbl_proxies.setItem(i, 4, QTableWidgetItem("Yes" if r.get("username") else "No"))

            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(0, 0, 0, 0)
            b_test = QToolButton()
            b_test.setText("Kiểm tra")
            b_test.setProperty("pid", r["id"])
            b_edit = QToolButton()
            b_edit.setText("Sửa")
            b_edit.setProperty("pid", r["id"])
            b_del = QToolButton()
            b_del.setText("Xoá")
            b_del.setProperty("pid", r["id"])
            for b in (b_test, b_edit, b_del): h.addWidget(b)
            h.addStretch(1)
            self.tbl_proxies.setCellWidget(i, 5, cell)

            b_test.clicked.connect(self.on_proxy_test)
            b_edit.clicked.connect(self.on_proxy_edit)
            b_del.clicked.connect(self.on_proxy_delete)

        self.tbl_proxies.resizeColumnsToContents()
        self.tbl_proxies.setAlternatingRowColors(True)
        self.tbl_proxies.setWordWrap(True)
        self.tbl_proxies.setTextElideMode(Qt.ElideNone)
        self.tbl_proxies.verticalHeader().setVisible(False)
        self.tbl_proxies.verticalHeader().setDefaultSectionSize(44)
        self.tbl_proxies.horizontalHeader().setStretchLastSection(False)

        hq = self.tbl_proxies.horizontalHeader()
        hq.setSectionsClickable(True)
        hq.setHighlightSections(False)

        hq.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        hq.setSectionResizeMode(1, QHeaderView.Stretch)  # Tên
        hq.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Loại
        hq.setSectionResizeMode(3, QHeaderView.Stretch)  # Host:Port
        hq.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Auth
        hq.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Hành động

    def on_proxy_add(self):
        dlg = ProxyDialog(self)
        if dlg.exec():
            payload = dlg.payload()
            if not payload["name"] or not payload["host"]:
                QMessageBox.warning(self, "Thiếu thông tin", "Tên và Host là bắt buộc.")
                return
            create_proxy(payload);
            self.refresh_proxies();
            self.refresh_profiles()

    def on_proxy_edit(self):
        pid = self.sender().property("pid")
        row = get_proxy(pid)
        if not row:
            QMessageBox.warning(self, "Lỗi", "Proxy không tồn tại.")
            return
        dlg = ProxyDialog(self, data=row)
        if dlg.exec():
            update_proxy(pid, dlg.payload())
            self.refresh_proxies();
            self.refresh_profiles()

    def on_proxy_delete(self):
        pid = self.sender().property("pid")
        if QMessageBox.question(self, "Xác nhận",
                                "Xóa proxy này? (Các profile đang gán sẽ set về Không dùng)") == QMessageBox.Yes:
            delete_proxy(pid);
            self.refresh_proxies();
            self.refresh_profiles()

    def on_proxy_test(self):
        from workers.proxy_check_worker import ProxyCheckWorker
        pid = self.sender().property("pid")
        row = get_proxy(pid)
        if not row:
            QMessageBox.warning(self, "Lỗi", "Proxy không tồn tại.")
            return
        self._btn_sender = self.sender();
        self._btn_sender.setEnabled(False)
        self.tester = ProxyCheckWorker(row)
        self.tester.finished_ok.connect(lambda msg: self._test_ok(msg))
        self.tester.failed.connect(lambda e: self._test_fail(e))
        self.tester.start()

    def _test_ok(self, msg: str):
        self._btn_sender.setEnabled(True)
        QMessageBox.information(self, "Proxy OK", msg)

    def _test_fail(self, err: str):
        self._btn_sender.setEnabled(True)
        QMessageBox.critical(self, "Proxy lỗi", err)

    def on_proxy_export(self):
        rows = list_proxies()
        path, _ = QFileDialog.getSaveFileName(self, "Export proxies", "proxies.json", "JSON (*.json)")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "OK", f"Đã export {len(rows)} proxies.")

    def on_proxy_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import proxies", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
            cnt = 0
            for it in items:
                payload = {
                    "name": (it.get("name") or "").strip(),
                    "proxy_type": it.get("proxy_type") or "http",
                    "host": (it.get("host") or "").strip(),
                    "port": int(it.get("port") or 8080),
                    "username": it.get("username"),
                    "password": it.get("password"),
                }
                if payload["name"] and payload["host"]:
                    create_proxy(payload);
                    cnt += 1
            self.refresh_proxies();
            self.refresh_profiles()
            QMessageBox.information(self, "OK", f"Đã import {cnt} proxies.")
        except Exception as e:
            QMessageBox.critical(self, "Import lỗi", str(e))

    def closeEvent(self, e):
        # stop all browser workers (đóng Chromium để ghi cookie/history)
        for pid, w in list(self.workers.items()):
            try:
                if hasattr(w, "stop"):
                    w.stop()
            except Exception:
                pass
        # dọn 3proxy wrappers còn sống
        try:
            from services.proxy_service import ProxyManager
            ProxyManager.stop_all()
        except Exception:
            pass
        super().closeEvent(e)
