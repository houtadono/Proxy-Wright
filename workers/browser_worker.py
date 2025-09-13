import os
import re
import time

import psutil
from PySide6.QtCore import QThread, Signal, Qt
from appdirs import user_data_dir

from config import APP_NAME, ORG_NAME


def profile_data_dir(profile_id: int) -> str:
    base = user_data_dir(APP_NAME, ORG_NAME)
    path = os.path.join(base, "profiles", str(profile_id))
    os.makedirs(path, exist_ok=True)
    return path


class BrowserWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)
    request_stop = Signal()
    request_force_kill = Signal()  # dùng khi cần ép mạnh

    def __init__(self, profile_id: int, proxy: dict | None):
        super().__init__()
        self.profile_id = profile_id
        self.proxy = proxy
        self._ctx = None
        self.request_force_kill.connect(self._on_request_force_kill, Qt.QueuedConnection)

    def stop(self):
        self.request_stop.emit()

    def force_kill(self):
        self.request_force_kill.emit()

    def run(self):
        try:
            user_dir = profile_data_dir(self.profile_id)

            from services.browser_service import open_profile_chromium
            def _on_ready(ctx):
                self._ctx = ctx

            open_profile_chromium(user_dir=user_dir, proxy=self.proxy, on_ready=_on_ready)
            self.finished_ok.emit(user_dir)
        except Exception as e:
            self.failed.emit(str(e))

    def _profile_dir_norm(self) -> str:
        base = user_data_dir(APP_NAME, ORG_NAME)
        target = os.path.abspath(os.path.join(base, "profiles", str(self.profile_id)))
        return os.path.normcase(os.path.normpath(target))

    def _match_profile_proc(self, p) -> bool:
        try:
            nm = (p.info["name"] or "").lower()
            if not any(k in nm for k in ("chrome", "chromium", "msedge")):
                return False
            cmd = p.info["cmdline"] or []
            joined = " ".join(cmd)
            m = re.search(r'--user-data-dir(?:=|\s+)(?:"([^"]+)"|(\S+))', joined, re.I)
            if not m: return False
            proc_dir = m.group(1) or m.group(2)
            proc_norm = os.path.normcase(os.path.normpath(os.path.abspath(proc_dir)))
            return proc_norm == self._profile_dir_norm()
        except Exception:
            return False

    def _on_request_force_kill(self):
        # Chạy sau khi đã thử close/WM_CLOSE mà vẫn còn
        # terminate -> kill
        time.sleep(0.3)
        for p in psutil.process_iter(["name", "cmdline"]):
            try:
                if self._match_profile_proc(p):
                    try:
                        p.terminate()
                    except Exception:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.5)
        for p in psutil.process_iter(["name", "cmdline"]):
            try:
                if self._match_profile_proc(p) and p.is_running():
                    try:
                        p.kill()
                    except Exception:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
