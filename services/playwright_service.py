import os, sys, platform, io, re, contextlib, threading, queue
from pathlib import Path
from core.paths import BROWSERS_DIR

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_REV_DIR_RE = re.compile(
    r"^(chromium|firefox|webkit|chrome|chrome-beta|msedge|msedge-beta|msedge-dev)(?:-with-symbols)?-(\d+)$")


class PlaywrightManager:
    def __init__(self) -> None:
        BROWSERS_DIR.mkdir(parents=True, exist_ok=True)

    # -------- Discovery --------
    def scan_versions(self) -> dict[str, int]:
        """
        Return latest installed revision for each browser under BROWSERS_DIR.
        Example: { "chromium": 1200, "firefox": 1180 }
        """
        latest: dict[str, int] = {}
        if not BROWSERS_DIR.exists():
            return latest
        for p in BROWSERS_DIR.iterdir():
            if not p.is_dir(): continue
            m = _REV_DIR_RE.match(p.name)
            if not m: continue
            name, rev = m.group(1), int(m.group(2))
            if rev > latest.get(name, -1):
                latest[name] = rev
        return latest

    def get_installed_versions(self) -> dict[str, int]:
        return self.scan_versions()

    def is_installed(self, browser: str = "chromium") -> bool:
        return browser in self.scan_versions()

    def _latest_base(self, browser: str) -> Path | None:
        v = self.scan_versions().get(browser)
        return (BROWSERS_DIR / f"{browser}-{v}") if v else None

    # -------- Install (in-process, streaming) --------
    def install_browser_events(self, browser: str = "chromium", with_deps: bool = False):
        """
        Generator:
          ("line", text:str)
          ("done", ok:bool)
        Chạy HOÀN TOÀN trong process hiện tại (không spawn exe) -> không thể nảy console/UI khác.
        """
        # Env ghi được
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)
        os.environ["TERM"] = "dumb"
        os.environ["PYTHONUTF8"] = "1"
        os.environ["PYTHONIOENCODING"] = "utf-8"

        argv = ["playwright", "install", browser]
        if with_deps and platform.system() == "Linux":
            argv.append("--with-deps")

        from playwright.__main__ import main as playwright_main
        q: "queue.Queue[object]" = queue.Queue()

        class _Catcher(io.TextIOBase):
            def __init__(self):
                self._buf = ""

            def write(self, s: str) -> int:
                self._buf += s
                # tách theo \r / \n để giữ tiến trình tải
                while True:
                    cr = self._buf.find("\r")
                    nl = self._buf.find("\n")
                    if cr == -1 and nl == -1:
                        break
                    cut = cr if (cr != -1 and (nl == -1 or cr < nl)) else nl
                    seg, self._buf = self._buf[:cut], self._buf[cut + 1:]
                    t = _ANSI_RE.sub("", seg).strip()
                    if t:
                        q.put(("line", t))
                return len(s)

            def flush_rest(self):
                if self._buf:
                    t = _ANSI_RE.sub("", self._buf).strip()
                    if t:
                        q.put(("line", t))
                    self._buf = ""

        def _runner():
            ok = False
            old_argv = sys.argv[:]
            catcher = _Catcher()
            try:
                sys.argv = argv
                with contextlib.redirect_stdout(catcher), contextlib.redirect_stderr(catcher):
                    try:
                        playwright_main()  # có thể sys.exit()
                    except SystemExit as e:
                        code = int(e.code or 0)
                        catcher.flush_rest()
                        q.put(("rc", code))
                        return
                catcher.flush_rest()
                q.put(("rc", 0))
            finally:
                sys.argv = old_argv

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

        ok = False
        while True:
            item = q.get()
            if isinstance(item, tuple) and item and item[0] == "rc":
                code = int(item[1])
                yield ("done", (ok or True) if code == 0 else False)
                break
            _, text = item
            if isinstance(text, str) and "[OK] Browser installed." in text:
                ok = True
            yield ("line", str(text))


    def install_browser_sync(self, browser: str = "chromium", with_deps: bool = False) -> bool:
        ok = False
        for kind, payload in self.install_browser_events(browser, with_deps):
            if kind == "done":
                ok = bool(payload)
        return ok

    def ensure_browser(self, browser: str = "chromium", auto_install: bool = False) -> None:
        """
        KHÔNG auto spawn process/console.
        - auto_install=False mặc định: chỉ kiểm tra, thiếu thì raise.
        - Nếu muốn auto cài silent: gọi install_browser_sync() ở nơi bạn chủ động (không phải lúc khởi động UI).
        """
        if not self.is_installed(browser):
            if auto_install:
                if not self.install_browser_sync(browser):
                    raise RuntimeError(f"Install {browser} failed.")
            else:
                raise RuntimeError(
                    f"Playwright {browser} is not installed in {BROWSERS_DIR}."
                )

    # -------- Executable path --------
    def get_executable_path(self, browser: str = "chromium") -> Path | None:
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
                return (base / "chrome-mac" / "Chromium.app/Contents/MacOS/Chromium").resolve()
            if browser.startswith("msedge"):
                return (base / "msedge-mac" / "Microsoft Edge.app/Contents/MacOS/Microsoft Edge").resolve()
            if browser == "firefox":
                return (base / "firefox" / "Firefox.app/Contents/MacOS/firefox").resolve()
            if browser == "webkit":
                return (base / "pw_run.sh").resolve()
        return None
