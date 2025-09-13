import shutil, os

dist_dir = "dist/ProxyWright/_internal/PySide6"
REMOVE_DIRS = [
    "translations",
    "qml",
    os.path.join("plugins", "imageformats"),
    os.path.join("plugins", "platformthemes"),
    os.path.join("plugins", "styles"),
]

for folder in REMOVE_DIRS:
    path = os.path.join(dist_dir, folder)
    if os.path.isdir(path):
        print(f"[CLEAN] remove {path}")
        shutil.rmtree(path, ignore_errors=True)
