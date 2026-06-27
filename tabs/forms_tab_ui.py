# tabs/forms_tab_ui.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QPushButton
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator


class FormsTabUI(QWidget):
    """Базовый UI-компонент вкладки управления формами."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Контейнер верхней панели инструментов
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_form)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_form)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_form)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Дерево для вывода списка зарегистрированных ERP-форм
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_entity')
        ])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 150)
        self.tree.itemDoubleClicked.connect(self.edit_form)
        layout.addWidget(self.tree)

        self.retranslate_ui()
        self.load_forms()

    def retranslate_ui(self):
        self.btn_add.setText(self.translator.tr('btn_add'))
        self.btn_edit.setText(self.translator.tr('btn_edit'))
        self.btn_delete.setText(self.translator.tr('btn_delete'))
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_entity')
        ])

    def load_forms(self):
        """Загружает плоский список форм из схемы meta."""
        sql = """
            SELECT f.id, f.cname, f.calias, f.ientitytypeid, et.cname as entity_name
            FROM meta.forms f
            LEFT JOIN meta.entitytypes et ON f.ientitytypeid = et.id
            ORDER BY f.cname
        """
        rows = self.db.execute_query(sql)
        self.tree.clear()

        for row in rows:
            from PySide6.QtWidgets import QTreeWidgetItem
            item = QTreeWidgetItem()
            item.setText(0, str(row[0]))
            item.setText(1, row[1] or "")
            item.setText(2, row[2] or "")
            item.setText(3, row[4] or "")
            item.setData(0, Qt.UserRole, row[0])
            self.tree.addTopLevelItem(item)

    def get_selected_id(self):
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def add_form(self): pass
    def edit_form(self): pass
    def delete_form(self): pass
