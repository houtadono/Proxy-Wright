from PySide6.QtCore import QThread, Signal
import socket
import json
import requests
from config import PROXY_TEST_URL, PROXY_TEST_TIMEOUT


class ProxyCheckWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, proxy: dict):
        super().__init__()
        self.proxy = proxy

    def _tcp_check(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(PROXY_TEST_TIMEOUT)
        try:
            s.connect((self.proxy['host'], int(self.proxy['port'])))
        finally:
            s.close()

    def _http_check(self) -> dict:
        scheme = 'socks5' if self.proxy.get('proxy_type') == 'socks5' else (self.proxy.get('proxy_type') or 'http')
        auth = ''
        if self.proxy.get('username') and self.proxy.get('password'):
            auth = f"{self.proxy['username']}:{self.proxy['password']}@"
        proxy_str = f"{scheme}://{auth}{self.proxy['host']}:{self.proxy['port']}"
        proxies = {
            'http': proxy_str,
            'https': proxy_str,
        }
        r = requests.get(PROXY_TEST_URL, proxies=proxies, timeout=PROXY_TEST_TIMEOUT)
        r.raise_for_status()
        return r.json() if r.headers.get('content-type', '').startswith('application/json') else {"ip": r.text}

    def run(self):
        try:
            self._tcp_check()
            data = self._http_check()
            self.finished_ok.emit(json.dumps({"ok": True, "ip": data.get("ip")}))
        except Exception as e:
            self.failed.emit(str(e))
