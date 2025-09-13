from PySide6.QtCore import QTranslator, QSettings
from .paths import get_setting_path, get_translations_dir


class AppSettings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.config_file = get_setting_path()
        # ép Qt lưu ở IniFormat
        self.settings = QSettings(str(self.config_file), QSettings.IniFormat)
        self.translator = QTranslator()

    def get(self, key: str, default=None):
        return self.settings.value(key, default)

    def set(self, key: str, value):
        self.settings.setValue(key, value)
        self.settings.sync()

    # ---- Lang helpers ----
    def get_lang(self) -> str:
        return self.get("lang", "en")

    def set_lang(self, lang: str):
        self.set("lang", lang)

    def apply_lang(self, app) -> str:
        lang = self.get_lang()
        if lang != "en":
            qm_path = get_translations_dir() / f"lang_{lang}.qm"
            if qm_path.exists():
                self.translator.load(str(qm_path))
                app.installTranslator(self.translator)
        return lang
