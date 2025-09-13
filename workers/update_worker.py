from __future__ import annotations
import logging
from PySide6.QtCore import QThread, Signal
from core.updater import UpdaterService, UpdateInfo

log = logging.getLogger(__name__)

class CheckUpdateWorker(QThread):
    finishedResult = Signal(object, object)  # (UpdateInfo|None, error|None)
    def __init__(self, service: UpdaterService, accept_prerelease: bool = False):
        super().__init__()
        self.service = service
        self.accept_prerelease = accept_prerelease
    def run(self):
        try:
            info = self.service.check_latest(accept_prerelease=self.accept_prerelease)
            self.finishedResult.emit(info, None)
        except Exception as e:
            log.exception("check_latest failed")
            self.finishedResult.emit(None, str(e))

class DownloadInstallWorker(QThread):
    progress = Signal(int, int)
    failed = Signal(str)
    startedInstalling = Signal()
    def __init__(self, service: UpdaterService, info: UpdateInfo, token: str | None = None):
        super().__init__()
        self.service, self.info, self.token = service, info, token
    def run(self):
        try:
            def cb(done, total): self.progress.emit(done, total)
            self.startedInstalling.emit()
            self.service.perform_update_flow(self.info, token=self.token, progress_cb=cb)
        except Exception as e:
            log.exception("download/install failed")
            self.failed.emit(str(e))
