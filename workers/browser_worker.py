from PySide6.QtCore import QThread, Signal, Qt

from core.paths import get_profile_data_dir


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
            user_dir = get_profile_data_dir(self.profile_id)

            from services.browser_service import open_profile_chromium
            def _on_ready(ctx):
                self._ctx = ctx

            open_profile_chromium(user_dir=user_dir, proxy=self.proxy, on_ready=_on_ready)
            self.finished_ok.emit(user_dir)
        except Exception as e:
            self.failed.emit(str(e))

    def _on_request_force_kill(self):
        pass
