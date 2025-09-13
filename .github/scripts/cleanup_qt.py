import shutil, os

dist_dir = "dist/ProxyProfileManager"
REMOVE_DIRS = ["translations", "qml", "imageformats", "platformthemes", "styles"]

for folder in REMOVE_DIRS:
    path = os.path.join(dist_dir, folder)
    if os.path.isdir(path):
        print(f"[CLEAN] remove {path}")
        shutil.rmtree(path)
