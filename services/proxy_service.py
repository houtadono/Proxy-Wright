import os
import socket
import subprocess
import tempfile
import time

import psutil

from core.paths import get_user_data_path, BIN_DIR


class ProxyManager:
    def __init__(self):
        self.bin_path = BIN_DIR/"3proxy.exe"
        if not self.bin_path.exists():
            raise FileNotFoundError(f"3proxy not found: {self.bin_path}")

        self.runtime_proxy_dir = get_user_data_path() / "runtime" / "3proxy"
        self.runtime_proxy_dir.mkdir(parents=True, exist_ok=True)

        self.processes: dict[int, tuple[subprocess.Popen, str, int]] = {}
        self._cleanup_startup()

    def _cleanup_startup(self):
        """Kill 3proxy còn sống dùng cfg trong runtime_proxy_dir và xoá tất cả .cfg."""
        # 1) kill mọi 3proxy có cmdline chứa runtime_proxy_dir
        try:
            for p in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    nm = (p.info["name"] or "").lower()
                    if "3proxy" not in nm:
                        continue
                    cmd = " ".join(p.info["cmdline"] or [])
                    if str(self.runtime_proxy_dir )in cmd:
                        try:
                            p.terminate()
                            p.wait(timeout=2)
                        except Exception:
                            try:
                                p.kill()
                            except Exception:
                                pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

        # 2) xoá tất cả cfg còn lại trong runtime_proxy_dir
        try:
            for cfg_file in self.runtime_proxy_dir.glob("*.cfg"):
                try:
                    cfg_file.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            pass

    def _pick_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def start_socks5_wrapper(self, proxy_id: int, socks_host: str, socks_port: int, username: str,
                             password: str) -> int:
        if proxy_id in self.processes:
            # đã có, trả lại port cũ
            return self.processes[proxy_id][2]

        local_port = self._pick_free_port()
        cfg_content = f"""\
fakeresolve
auth iponly
allow * 127.0.0.1
parent 1000 socks5+ {socks_host} {socks_port} {username} {password}
socks -p{local_port} -i127.0.0.1
"""
        cfg_file = tempfile.NamedTemporaryFile(delete=False, suffix=".cfg")
        cfg_file.write(cfg_content.encode("utf-8"))
        cfg_file.close()

        proc = subprocess.Popen(
            [self.bin_path, cfg_file.name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)  # ẩn console trên Windows
        )
        self.processes[proxy_id] = (proc, cfg_file.name, local_port)
        return local_port

    def stop_socks5_wrapper(self, proxy_id: int):
        tup = self.processes.pop(proxy_id, None)
        if not tup:
            return
        proc, cfg_file, _ = tup
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=3)
            except Exception:
                pass
        try:
            time.sleep(0.2)
            os.remove(cfg_file)
        except Exception:
            pass

    @staticmethod
    def stop_all():
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if "3proxy" in (p.info["name"] or "").lower():
                    print(f"[ProxyManager] Kill {p.pid}")
                    p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
