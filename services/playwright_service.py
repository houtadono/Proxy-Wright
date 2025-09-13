import os, re, sys, subprocess


class PlaywrightManager:
    def __init__(self, app_dir: str):
        self.browser_dir = os.path.join(app_dir, "browsers")
        os.makedirs(self.browser_dir, exist_ok=True)

    def scan_versions(self) -> dict:
        versions = {}
        for name in os.listdir(self.browser_dir):
            m = re.match(
                r"^(chromium|firefox|webkit|chrome|chrome-beta|msedge|msedge-beta|msedge-dev)(?:-with-symbols)?-(\d+)$",
                name)
            if m:
                versions[m.group(1)] = int(m.group(2))
        return versions

    def get_installed_versions(self) -> dict:
        return self.scan_versions()

    def ensure_browser_installed(self, browser="chromium", force=False) -> int | None:
        versions = self.get_installed_versions()
        if force or browser not in versions:
            env = os.environ.copy()
            env["PLAYWRIGHT_BROWSERS_PATH"] = self.browser_dir
            python_exe = sys._base_executable if hasattr(sys, "_base_executable") else sys.executable

            subprocess.run(
                [python_exe, "-m", "playwright", "install", browser],
                check=True,
                env=env
            )
            versions = self.get_installed_versions()
        return versions.get(browser)

    def get_executable_path(self, browser: str) -> str | None:
        """
        Lấy đường dẫn binary của browser đã cài trong browsers/.
        Trả về None nếu chưa cài.
        """
        versions = self.get_installed_versions()
        ver = versions.get(browser)
        if not ver:
            return None

        base = os.path.join(self.browser_dir, f"{browser}-{ver}")

        # mapping tuỳ OS và browser
        if sys.platform.startswith("win"):
            if browser in ("chromium", "chrome", "chrome-beta"):
                return os.path.join(base, "chrome-win", "chrome.exe")
            elif browser.startswith("msedge"):
                return os.path.join(base, "msedge-win", "msedge.exe")
            elif browser == "firefox":
                return os.path.join(base, "firefox", "firefox.exe")
            elif browser == "webkit":
                return os.path.join(base, "pw_run.sh")
        elif sys.platform.startswith("linux"):
            if browser in ("chromium", "chrome", "chrome-beta"):
                return os.path.join(base, "chrome-linux", "chrome")
            elif browser.startswith("msedge"):
                return os.path.join(base, "msedge-linux", "msedge")
            elif browser == "firefox":
                return os.path.join(base, "firefox", "firefox")
            elif browser == "webkit":
                return os.path.join(base, "pw_run.sh")
        elif sys.platform == "darwin":
            if browser in ("chromium", "chrome", "chrome-beta"):
                return os.path.join(base, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium")
            elif browser.startswith("msedge"):
                return os.path.join(base, "msedge-mac", "Microsoft Edge.app", "Contents", "MacOS", "Microsoft Edge")
            elif browser == "firefox":
                return os.path.join(base, "firefox", "Firefox.app", "Contents", "MacOS", "firefox")
            elif browser == "webkit":
                return os.path.join(base, "pw_run.sh")
        return None
