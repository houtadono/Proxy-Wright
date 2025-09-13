from __future__ import annotations
import argparse, os, sys, time, shutil, zipfile, subprocess
from pathlib import Path


def wait_for_pid_exit(pid: int, timeout_sec: int = 60) -> None:
    deadline = time.time() + timeout_sec
    if os.name == "nt":
        # Windows: dùng WinAPI để wait PID (không cần psutil)
        import ctypes
        from ctypes import wintypes
        SYNCHRONIZE = 0x00100000
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE
        WaitForSingleObject = kernel32.WaitForSingleObject
        WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        CloseHandle = kernel32.CloseHandle
        handle = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            # chờ tối đa timeout
            ms = int(max(0, timeout_sec) * 1000)
            WaitForSingleObject(handle, ms)
            CloseHandle(handle)
        else:
            # fallback polling nếu không mở được handle
            while time.time() < deadline:
                try:
                    # Nếu process còn sống, tasklist sẽ thấy; nhưng polling đơn giản:
                    import subprocess
                    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                    if str(pid) not in out.stdout:
                        break
                except Exception:
                    break
                time.sleep(0.2)
    else:
        # POSIX: os.kill(pid, 0) ném OSError nếu không tồn tại
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except OSError:
                break


def unzip_all(src_zip: Path, dst_dir: Path) -> Path:
    """Giải nén zip vào dst_dir, trả về thư mục gốc chứa nội dung mới."""
    with zipfile.ZipFile(src_zip, "r") as z:
        z.extractall(dst_dir)
    # nếu zip có 1 thư mục root, dùng nó; nếu không, dùng dst_dir
    entries = [p for p in dst_dir.iterdir()]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dst_dir


def copy_or_replace_tree(src_dir: Path, dst_dir: Path) -> None:
    tmp_new = dst_dir.with_suffix(".new")
    backup = dst_dir.with_suffix(".bak")
    if tmp_new.exists():
        shutil.rmtree(tmp_new, ignore_errors=True)
    tmp_new.mkdir(parents=True, exist_ok=True)

    # copy toàn bộ src -> .new
    for item in src_dir.iterdir():
        target = tmp_new / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)

    # đổi chỗ atomic best-effort
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    if dst_dir.exists():
        try:
            dst_dir.replace(backup)  # rename nhanh
        except Exception:
            shutil.rmtree(backup, ignore_errors=True)
            shutil.copytree(dst_dir, backup, dirs_exist_ok=True)
            shutil.rmtree(dst_dir, ignore_errors=True)
    try:
        tmp_new.replace(dst_dir)
    except Exception:
        # fallback: copy
        shutil.copytree(tmp_new, dst_dir, dirs_exist_ok=True)
        shutil.rmtree(tmp_new, ignore_errors=True)
    shutil.rmtree(backup, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Portable updater helper")
    ap.add_argument("--pid", type=int, required=True, help="PID của app chính")
    ap.add_argument("--src", required=True, help="Đường dẫn ZIP hoặc thư mục build mới")
    ap.add_argument("--dst", required=True, help="Thư mục app hiện tại (để thay thế)")
    ap.add_argument("--exe", default="ProxyWright.exe", help="Tên exe để relaunch")
    ap.add_argument("--unzip", action="store_true", help="Giải nén nếu --src là .zip")
    ap.add_argument("--wait", type=int, default=60, help="Thời gian chờ app chính thoát (giây)")
    args = ap.parse_args()

    # 1) chờ app chính thoát
    wait_for_pid_exit(args.pid, timeout_sec=args.wait)

    src = Path(args.src).resolve()
    dst = Path(args.dst).resolve()
    work = dst.parent / (dst.name + "_incoming")
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    # 2) chuẩn bị bản mới
    src_ready: Path
    if args.unzip and src.suffix.lower() == ".zip":
        src_ready = unzip_all(src, work)
    else:
        # copy y nguyên thư mục src vào work
        for item in src.iterdir():
            target = work / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        src_ready = work

    # 3) thay thế
    copy_or_replace_tree(src_ready, dst)

    # 4) relaunch
    exe_path = dst / args.exe
    if exe_path.exists():
        try:
            subprocess.Popen([str(exe_path)], cwd=str(dst), close_fds=True)
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
