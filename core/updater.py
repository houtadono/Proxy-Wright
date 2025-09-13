import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import requests
from packaging.version import Version

from config import APP_NAME, APP_VERSION, APP_UPDATE_URL, REPO_WEB_URL
from core.paths import get_app_path


@dataclass
class UpdateInfo:
    tag: str
    version: Version
    notes: str
    asset_name: str
    asset_url: str
    is_prerelease: bool
    published_at: str | None = None
    sums_url: str | None = None


def exe_name_default() -> str:
    """Tên exe mặc định để relaunch sau update (portable)."""
    return f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME


class UpdaterService:
    def __init__(
            self,
            app_dir: Optional[Path] = None,
            current_version: str = APP_VERSION,
            app_name: str = APP_NAME,
            update_api_url: str = APP_UPDATE_URL,
            repo_web_url: Optional[str] = REPO_WEB_URL,
            proxies: Optional[dict] = None,
            marker_installed_filename: str = ".installed",
    ) -> None:
        self.app_dir = Path(app_dir) if app_dir else get_app_path()
        self.current_version = Version(str(current_version).lstrip("vV"))
        self.app_name = app_name
        self.update_api_url = update_api_url
        self.repo_web_url = repo_web_url
        self.proxies = proxies
        self.marker_installed_filename = marker_installed_filename

    # ---------- Discovery ----------
    def is_installed_mode(self) -> bool:
        return (self.app_dir / self.marker_installed_filename).exists()

    def _pick_asset(self, assets: list[dict], prefer_installer: bool) -> Optional[dict]:
        """
        - Installer: '<AppName>-(Setup|Installer).*\\.exe'
        - Portable:  '<AppName>-Portable-.*\\.zip'
        """
        if prefer_installer:
            pat = re.compile(rf"{re.escape(self.app_name)}-(Setup|Installer).*\.exe$", re.I)
        else:
            pat = re.compile(rf"{re.escape(self.app_name)}-Portable-.*\.zip$", re.I)

        for a in assets:
            if a.get("state") == "uploaded" and pat.search(a.get("name", "")):
                return a
        if prefer_installer:
            # fallback về portable nếu không có installer
            for a in assets:
                if a.get("state") == "uploaded" and re.search(
                        rf"{re.escape(self.app_name)}-Portable-.*\.zip$", a.get("name", ""), re.I
                ):
                    return a
        return None

    def _find_sums_asset(self, assets: list[dict]) -> str | None:
        for a in assets:
            n = (a.get("name") or "").lower()
            if n == "sha256sums.txt":
                return a.get("browser_download_url")
        return None

    def check_latest(
            self,
            accept_prerelease: bool = False,
            prefer_installer: Optional[bool] = None,
            token: Optional[str] = None,
            timeout: int = 20,
    ) -> Optional[UpdateInfo]:
        """
        Trả về UpdateInfo nếu có bản mới hơn, ngược lại None.
        """
        if prefer_installer is None:
            prefer_installer = self.is_installed_mode()

        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        r = requests.get(self.update_api_url, headers=headers, timeout=timeout, proxies=self.proxies)
        r.raise_for_status()
        releases = r.json()

        best: Optional[UpdateInfo] = None

        for rel in releases:
            if (not accept_prerelease) and rel.get("prerelease"):
                continue
            tag = (rel.get("tag_name") or "").strip()
            tag_norm = tag.lstrip("vV")

            try:
                ver = Version(tag_norm)
            except Exception:
                continue

            assets = rel.get("assets", [])
            asset = self._pick_asset(assets, prefer_installer=prefer_installer)
            if not asset:
                continue

            ui = UpdateInfo(
                tag=tag,
                version=ver,
                notes=rel.get("body") or "",
                asset_name=asset.get("name", ""),
                asset_url=asset.get("browser_download_url", ""),
                is_prerelease=bool(rel.get("prerelease")),
                published_at=rel.get("published_at"),
                sums_url=self._find_sums_asset(assets),
            )

            if not best or ui.version > best.version:
                best = ui

        if not best:
            return None
        if best.version <= self.current_version:
            return None
        return best

    # ---------- Download ----------
    def download(
            self,
            url: str,
            dest: Path,
            token: Optional[str] = None,
            progress_cb: Optional[Callable[[int, int], None]] = None,
            timeout: int = 120,
    ) -> Path:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        with requests.get(url, headers=headers, stream=True, timeout=timeout, proxies=self.proxies) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1024 * 128):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        progress_cb(done, total)
            tmp.replace(dest)
        return dest

    # ---------- Checksums ----------
    def _download_text(self, url: str, token: str | None = None, timeout: int = 30) -> str:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers, timeout=timeout, proxies=self.proxies)
        r.raise_for_status()
        return r.text

    @staticmethod
    def _parse_sums(text: str) -> dict[str, str]:
        """
        Parse định dạng: "<sha256>␠␠<filename>" mỗi dòng.
        Trả về map theo basename: { 'ProxyWright-Portable-v1.2.3.zip': 'abcd...' }.
        """
        out: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            h = parts[0].lower()
            if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
                continue
            fname = " ".join(parts[1:]).strip()
            out[Path(fname).name] = h
        return out

    @staticmethod
    def _sha256sum(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    # ---------- Apply (Installer) ----------
    def apply_with_installer(self, setup_exe: Path, extra_args: Optional[list[str]] = None) -> None:
        args = [
            str(setup_exe),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            f'/LOG="{setup_exe.with_suffix(".log")}"',
        ]
        if extra_args:
            args += extra_args
        subprocess.Popen(args, close_fds=True)
        os._exit(0)

    # ---------- Apply (Portable + Updater.exe) ----------
    def apply_portable(self, zip_path: Path, exe_name: Optional[str] = None) -> None:
        """
        Yêu cầu có Updater.exe đặt cạnh app (self.app_dir / 'Updater.exe').
        """
        updater = self.app_dir / ("Updater.exe" if sys.platform.startswith("win") else "updater")
        if not updater.exists():
            raise RuntimeError(f"Updater helper not found: {updater}")

        if exe_name is None:
            exe_name = exe_name_default()

        args = [
            str(updater),
            "--pid",
            str(os.getpid()),
            "--src",
            str(zip_path),
            "--dst",
            str(self.app_dir),
            "--exe",
            exe_name,
            "--unzip",
        ]
        subprocess.Popen(args, cwd=str(self.app_dir), close_fds=True)
        os._exit(0)

    # ---------- High-level helper ----------
    def perform_update_flow(
            self,
            info: UpdateInfo,
            token: Optional[str] = None,
            progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Tải asset -> (tuỳ chọn) verify SHA256 -> áp dụng update (installer/portable) -> thoát app.
        """
        temp_dir = Path(tempfile.gettempdir())
        dest = temp_dir / info.asset_name

        # 1) Lấy expected checksum nếu có
        expected_hash: str | None = None
        if info.sums_url:
            try:
                sums_text = self._download_text(info.sums_url, token=token)
                sums_map = self._parse_sums(sums_text)
                expected_hash = sums_map.get(info.asset_name)
            except Exception:
                # Không có/không tải được checksum -> bỏ qua verify (tuỳ chính sách)
                expected_hash = None

        # 2) Tải file update
        self.download(info.asset_url, dest, token=token, progress_cb=progress_cb)

        # 3) Verify checksum nếu có
        if expected_hash:
            actual = self._sha256sum(dest)
            if actual.lower() != expected_hash.lower():
                try:
                    dest.unlink(missing_ok=True)
                except Exception:
                    pass
                raise RuntimeError(
                    f"Checksum mismatch for {info.asset_name}.\nExpected: {expected_hash}\nGot: {actual}"
                )

        # 4) Áp dụng cập nhật
        if dest.suffix.lower() == ".exe":
            self.apply_with_installer(dest)
        else:
            self.apply_portable(dest)
