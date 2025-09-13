import sys
from PySide6.QtWidgets import QApplication

from core.settings import AppSettings
from data.db import init_db
from ui.main_window import MainWindow

try:
    from qt_material import apply_stylesheet
except ImportError:
    apply_stylesheet = None

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    settings = AppSettings()
    settings.apply_lang(app)

    if apply_stylesheet:
        apply_stylesheet(app, theme="dark_cyan.xml", invert_secondary=True)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
