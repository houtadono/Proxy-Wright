from pathlib import Path
from typing import Optional, Callable

from services.playwright_service import PlaywrightManager
from services.proxy_service import ProxyManager

proxy_manager = ProxyManager()


def open_profile_chromium(user_dir: Path, proxy: dict | None = None, on_ready: Optional[Callable] = None):
    """
    Open a Chromium profile using Playwright, with optional proxy support.

    :param user_dir: Path to the user data directory for the Chromium profile
    :param proxy: Proxy configuration dict (optional)
    :param on_ready: Callback called with the Playwright context once it is ready
    """
    from playwright.sync_api import sync_playwright
    from config import DEFAULT_START_URL
    proxy_config = None
    started_wrapper = False

    if proxy:
        scheme = (proxy.get("proxy_type") or "http").lower()
        host, port = proxy["host"], int(proxy["port"] or 8080)
        user, pwd = proxy.get("username"), proxy.get("password")

        if scheme == "socks5" and user:
            # Start local wrapper for authenticated SOCKS5 proxies
            p = proxy_manager.start_socks5_wrapper(
                proxy_id=proxy["id"], socks_host=host, socks_port=port, username=user, password=pwd or ""
            )
            proxy_config = {"server": f"socks5://127.0.0.1:{p}"}
            started_wrapper = True
        else:
            proxy_config = {"server": f"{scheme}://{host}:{port}"}
            if user and scheme != "socks5":
                proxy_config["username"] = user
                proxy_config["password"] = pwd

    try:
        manager = PlaywrightManager()

        with sync_playwright() as pw:
            exec_path = manager.get_executable_path("chromium")
            ctx = pw.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                proxy=proxy_config,
                executable_path=exec_path,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--proxy-bypass-list=<-loopback>,127.0.0.1;localhost",
                ],
                ignore_default_args=["--enable-automation"],
            )
            if callable(on_ready):
                on_ready(ctx)

            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                page.goto(DEFAULT_START_URL, wait_until="domcontentloaded", timeout=30000)
            except TimeoutError:
                print("[browser] start URL timeout, continue anyway...")

            try:
                ctx.wait_for_event("close", timeout=0)
            except:
                pass
    except Exception as e:
        # Common error hints
        msg = str(e)
        if "ERR_TUNNEL_CONNECTION_FAILED" in msg:
            raise RuntimeError(
                "Failed to connect through proxy (ERR_TUNNEL_CONNECTION_FAILED). "
                "Please check the proxy settings, username/password, or IP whitelist."
            )
        raise
    finally:
        if started_wrapper and proxy:
            try:
                proxy_manager.stop_socks5_wrapper(proxy["id"])
            except Exception:
                pass
