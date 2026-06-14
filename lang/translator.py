# lang/translator.py
import threading
from database import DatabaseService

class Translator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db = DatabaseService()
        self.current_language = 'ru'
        self._cache = {}
        self._loaded = False
        self._initialized = True

    def _load_all(self):
        rows = self.db.execute_query("SELECT label_key, language, translation FROM lang.translations")
        for key, lang, text in rows:
            self._cache[(key, lang)] = text
        self._loaded = True

    def set_language(self, lang_code):
        self.current_language = lang_code

    def tr(self, key):
        if not self._loaded:
            self._load_all()
        if (key, self.current_language) in self._cache:
            return self._cache[(key, self.current_language)]
        if (key, 'en') in self._cache:
            return self._cache[(key, 'en')]
        return key

    def refresh(self):
        self._cache.clear()
        self._loaded = False
        # переводы будут перезагружены при следующем вызове tr()