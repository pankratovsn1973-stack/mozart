# tabs/entity_subtabs/import_tab.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from database import DatabaseService
from lang.local_translator import LocalTranslator
from mozart_import.dialogs.profile_manager_dialog import ProfileManagerDialog


class ImportTab(QWidget):
    """Вкладка импорта для конкретной сущности."""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_entity_id = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.btn_manage = QPushButton(self.translator.tr('btn_start_import_designer'))
        self.btn_manage.clicked.connect(self.open_profile_manager)
        layout.addWidget(self.btn_manage)
        layout.addStretch()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_manage.setText(self.translator.tr('btn_start_import_designer'))

    def set_entity_id(self, entity_id):
        self.current_entity_id = entity_id

    def open_profile_manager(self):
        """Открывает диалог управления профилями импорта."""
        dlg = ProfileManagerDialog(self.db, self)
        dlg.exec_()