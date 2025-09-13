import os, shutil, sys
from pathlib import Path

dist_dir = Path("dist/ProxyProfileManager")
internal_dir = dist_dir / "_internal"
internal_dir.mkdir(parents=True, exist_ok=True)

if sys.platform.startswith("win"):
    base = Path(os.environ["LOCALAPPDATA"]) / "ms-playwright"
else:
    base = Path.home() / ".cache" / "ms-playwright"

chromiums = sorted(base.glob("chromium-*"))
if not chromiums:
    raise RuntimeError(f"Không tìm thấy Chromium trong {base}")

chromium_dir = chromiums[-1]
target = internal_dir / chromium_dir.name
print(f"[COPY] Chromium: {chromium_dir} -> {target}")
shutil.copytree(chromium_dir, target, dirs_exist_ok=True)

# Copy 3proxy.exe
src_proxy = Path("bin/3proxy.exe")
if src_proxy.exists():
    shutil.copy(src_proxy, internal_dir / "3proxy.exe")
    print(f"[COPY] 3proxy.exe -> {internal_dir}")
else:
    print("[WARN] Không tìm thấy bin/3proxy.exe")
