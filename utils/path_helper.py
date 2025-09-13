def get_app_dir() -> str:
    """
    Trả về thư mục gốc của app:
    - Dev: thư mục hiện tại (.)
    - PyInstaller onefile: sys._MEIPASS (thư mục tạm)
    - PyInstaller onedir: thư mục chứa exe
    """
    import sys, os
    if getattr(sys, "frozen", False):  # đang chạy từ PyInstaller
        if hasattr(sys, "_MEIPASS"):  # onefile
            return sys._MEIPASS
        else:  # onedir
            return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")
