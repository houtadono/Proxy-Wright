import sys
from PySide6.QtWidgets import QApplication
from db import init_db
from ui.main_window import MainWindow

# NEW
try:
    from qt_material import apply_stylesheet
except ImportError:
    apply_stylesheet = None

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)

    # NEW: theme material (tuỳ chọn)
    if apply_stylesheet:
        # gợi ý: dark_cyan / dark_teal / light_blue.xml ...
        apply_stylesheet(app, theme="dark_cyan.xml", invert_secondary=True)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
