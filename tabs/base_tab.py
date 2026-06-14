
# tabs/base_tab.py
# tabs/base_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from database import DatabaseService
from lang.local_translator import LocalTranslator


class BaseTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def show_error(self, message):
        QMessageBox.critical(self, self.translator.tr('error'), message)

    def show_info(self, message):
        QMessageBox.information(self, self.translator.tr('info'), message)

    def show_warning(self, message):
        QMessageBox.warning(self, self.translator.tr('warning'), message)

    def refresh(self):
        pass

    def retranslate_ui(self):
        """Переопределяется в подклассах."""
        pass