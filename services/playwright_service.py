import os
import re
import sys
import subprocess
import platform
from pathlib import Path

from core.paths import BROWSERS_DIR

_REV_DIR_RE = re.compile(
    r"^(chromium|firefox|webkit|chrome|chrome-beta|msedge|msedge-beta|msedge-dev)(?:-with-symbols)?-(\d+)$"
)

ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

class PlaywrightManager:
    def __init__(self) -> None:
        BROWSERS_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------------------
    # Discovery
    # ----------------------------
    def scan_versions(self) -> dict[str, int]:
        """
        Return latest installed revision for each browser under BROWSERS_DIR.
        Example: { "chromium": 1200, "firefox": 1180 }
        """
        latest: dict[str, int] = {}
        if not BROWSERS_DIR.exists():
            return latest

        for p in BROWSERS_DIR.iterdir():
            if not p.is_dir():
                continue
            m = _REV_DIR_RE.match(p.name)
            if not m:
                continue
            name, rev = m.group(1), int(m.group(2))
            if rev > latest.get(name, -1):
                latest[name] = rev
        return latest

    def get_installed_versions(self) -> dict[str, int]:
        return self.scan_versions()

    def is_installed(self, browser: str = "chromium") -> bool:
        return browser in self.scan_versions()

    def _latest_base(self, browser: str) -> Path | None:
        """Return path to <browser>-<latest_rev> dir."""
        versions = self.scan_versions()
        rev = versions.get(browser)
        if not rev:
            return None
        return BROWSERS_DIR / f"{browser}-{rev}"

    # ----------------------------
    # Install
    # ----------------------------
    def _env_with_path(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)
        return env

    def install_browser(self, browser: str = "chromium", with_deps: bool = False) -> None:
        """
        Install a Playwright runtime browser into BROWSERS_DIR.
        Synchronous; raises if installation fails.
        """
        cmd = [sys.executable, "-m", "playwright", "install", browser]
        if with_deps and platform.system() == "Linux":
            cmd.append("--with-deps")
        subprocess.run(cmd, check=True, env=self._env_with_path())

    def install_browser_events(self, browser: str = "chromium", with_deps: bool = False):
        """
        Generator of structured events during installation.
        Yields tuples:
          ("line", text:str)                       # for normal log lines
          ("done", ok:bool)                        # at the end
        """
        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)
        env["TERM"] = "dumb"
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        cmd = [sys.executable, "-m", "playwright", "install", browser]
        if with_deps and platform.system() == "Linux":
            cmd.append("--with-deps")

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0

        # read as bytes to handle '\r' updates; we will decode manually
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env,
            creationflags=creationflags,
        )

        ok = False
        try:
            assert proc.stdout is not None
            buffer = b""
            while True:
                chunk = proc.stdout.read(1)
                if not chunk:
                    break
                buffer += chunk

                while True:
                    cr = buffer.find(b"\r")
                    nl = buffer.find(b"\n")
                    cut = -1
                    is_cr = False
                    if cr != -1 and (nl == -1 or cr < nl):
                        cut, is_cr = cr, True
                    elif nl != -1:
                        cut = nl
                    else:
                        break

                    seg = buffer[:cut]
                    buffer = buffer[cut + 1:]

                    text = ANSI_RE.sub("", seg.decode("utf-8", "replace")).strip()

                    if not text:
                        continue

                    if "[OK] Browser installed." in text:
                        ok = True
                    yield ("line", text)

        finally:
            rc = proc.wait()
            if rc != 0:
                yield ("line", f"[ERROR] playwright install exited with code {rc}")
                yield ("done", False)
            else:
                yield ("done", ok or rc == 0)

    def ensure_browser(self, browser: str = "chromium", auto_install: bool = True) -> None:
        """
        Ensure at least one browser is available.
        - If missing and auto_install=True: install automatically.
        - If missing and auto_install=False: raise RuntimeError.
        """
        if not self.is_installed(browser):
            if auto_install:
                self.install_browser(browser=browser)
            else:
                raise RuntimeError(
                    f"Playwright {browser} is not installed in {BROWSERS_DIR}. "
                    "Please install from Settings → Install Browser."
                )

    # ----------------------------
    # Executable path
    # ----------------------------
    def get_executable_path(self, browser: str = "chromium") -> Path | None:
        """
        Return the platform-specific executable path for a given browser,
        or None if not installed.
        """
        base = self._latest_base(browser)
        if not base:
            return None

        sys_plat = sys.platform
        if sys_plat.startswith("win"):
            if browser in ("chromium", "chrome", "chrome-beta"):
                return (base / "chrome-win" / "chrome.exe").resolve()
            if browser.startswith("msedge"):
                return (base / "msedge-win" / "msedge.exe").resolve()
            if browser == "firefox":
                return (base / "firefox" / "firefox.exe").resolve()
            if browser == "webkit":
                # WebKit is not provided on Windows; Playwright uses a runner script elsewhere.
                return (base / "pw_run.sh").resolve()
        elif sys_plat.startswith("linux"):
            if browser in ("chromium", "chrome", "chrome-beta"):
                return (base / "chrome-linux" / "chrome").resolve()
            if browser.startswith("msedge"):
                return (base / "msedge-linux" / "msedge").resolve()
            if browser == "firefox":
                return (base / "firefox" / "firefox").resolve()
            if browser == "webkit":
                return (base / "pw_run.sh").resolve()
        elif sys_plat == "darwin":
            if browser in ("chromium", "chrome", "chrome-beta"):
                return (base / "chrome-mac" / "Chromium.app" / "Contents" / "MacOS" / "Chromium").resolve()
            if browser.startswith("msedge"):
                return (base / "msedge-mac" / "Microsoft Edge.app" / "Contents" / "MacOS" / "Microsoft Edge").resolve()
            if browser == "firefox":
                return (base / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox").resolve()
            if browser == "webkit":
                return (base / "pw_run.sh").resolve()
        return None
