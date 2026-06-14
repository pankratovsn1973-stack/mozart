# /home/sergey/Documents/configurate/ide_db_work.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton
from PySide6.QtCore import Qt

from database import DatabaseService
from tabs import (
    BalanceUnitsTab, UsersRolesTab, EntitiesTab,
    DocumentsTab, DataViewTab, RelationsTab, ImportTab,
    ClassTemplatesTab, FormsTab
)
from lang.local_translator import LocalTranslator


class DBWorkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('window_title_db_work'))
        self.resize(1300, 800)

        self.db = DatabaseService()

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.tabs.addTab(BalanceUnitsTab(self, db=self.db), self.translator.tr('tab_balance_units'))
        self.tabs.addTab(UsersRolesTab(self, db=self.db), self.translator.tr('tab_users_roles'))
        self.tabs.addTab(EntitiesTab(self, db=self.db), self.translator.tr('tab_entities'))
        self.tabs.addTab(DocumentsTab(self, db=self.db), self.translator.tr('tab_documents'))
        self.tabs.addTab(DataViewTab(self, db=self.db), self.translator.tr('tab_data_view'))
        self.tabs.addTab(RelationsTab(self, db=self.db), self.translator.tr('tab_relations'))
        self.tabs.addTab(ImportTab(self, db=self.db), self.translator.tr('tab_import'))
        self.tabs.addTab(ClassTemplatesTab(self, db=self.db), self.translator.tr('tab_class_templates'))
        self.tabs.addTab(FormsTab(self, db=self.db), self.translator.tr('tab_forms'))  # Новая вкладка

        layout.addWidget(self.tabs)

        self.btn_close = QPushButton(self.translator.tr('btn_close'))
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close, alignment=Qt.AlignRight)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.tr('window_title_db_work'))
        self.tabs.setTabText(0, self.translator.tr('tab_balance_units'))
        self.tabs.setTabText(1, self.translator.tr('tab_users_roles'))
        self.tabs.setTabText(2, self.translator.tr('tab_entities'))
        self.tabs.setTabText(3, self.translator.tr('tab_documents'))
        self.tabs.setTabText(4, self.translator.tr('tab_data_view'))
        self.tabs.setTabText(5, self.translator.tr('tab_relations'))
        self.tabs.setTabText(6, self.translator.tr('tab_import'))
        self.tabs.setTabText(7, self.translator.tr('tab_class_templates'))
        self.tabs.setTabText(8, self.translator.tr('tab_forms'))  # Новая вкладка
        self.btn_close.setText(self.translator.tr('btn_close'))

        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, 'retranslate_ui'):
                widget.retranslate_ui()