# tabs/entity_subtabs/routes_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from database import DatabaseService
from lang.local_translator import LocalTranslator


class RoutesTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_entity_id = None
        layout = QVBoxLayout(self)
        self.label_status = QLabel(self.translator.tr('routes_in_development'))
        layout.addWidget(self.label_status)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.label_status.setText(self.translator.tr('routes_in_development'))

    def set_entity_id(self, entity_id):
        self.current_entity_id = entity_id