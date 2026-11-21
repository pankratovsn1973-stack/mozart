# Полный путь: dialogs/class_group_manager_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from .class_group_edit_dialog import ClassGroupEditDialog


class ClassGroupManagerDialog(QDialog):
    """Менеджер иерархической структуры категорий с фильтром и защитой удаления."""

    def __init__(self, parent=None, db: DatabaseService = None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.current_selected_id = None

        self.setWindowTitle(self.translator.tr('title_group_manager'))
        self.resize(650, 550)
        self.setup_ui()
        self.load_groups()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: Поисковый фильтр TXT1 и кнопки CRUD
        top_layout = QHBoxLayout()
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Фильтр групп...")
        self.txt_filter.textChanged.connect(self.load_groups)  # Фильтрация «на лету»
        top_layout.addWidget(self.txt_filter)

        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_group)
        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_group)
        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_group)

        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_delete)
        layout.addLayout(top_layout)

        # Дерево категорий
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([self.translator.tr('field_name'), self.translator.tr('field_alias')])
        self.tree.itemSelectionChanged.connect(self.on_item_selected)
        self.tree.itemDoubleClicked.connect(self.edit_group)
        layout.addWidget(self.tree)

    def on_item_selected(self):
        item = self.tree.currentItem()
        self.current_selected_id = item.data(0, Qt.UserRole) if item else None

    def load_groups(self):
        """Загрузка дерева групп с учетом текстового фильтра TXT1."""
        self.tree.clear()
        filter_text = self.txt_filter.text().strip().lower()

        sql = "SELECT id, parent_id, c_name, c_alias FROM class_erp.class_category ORDER BY i_sortorder, id;"
        rows = self.db.execute_query(sql) or []
        nodes = {}
        to_add = []

        for r_id, p_id, c_name, c_alias in rows:
            item = QTreeWidgetItem()
            item.setText(0, c_name)
            item.setText(1, c_alias)
            item.setData(0, Qt.UserRole, r_id)
            nodes[r_id] = item

            # Логика фильтрации: узел подходит, если совпадает имя или алиас
            matches = (not filter_text
                       or filter_text in c_name.lower()
                       or filter_text in (c_alias or '').lower())

            if p_id and p_id in nodes:
                nodes[p_id].addChild(item)
            else:
                to_add.append((item, matches))

        for item, matches in to_add:
            # Корневые добавляем на сцену всегда (чтобы не потерять детей)
            self.tree.addTopLevelItem(item)

        # Прячем узлы, не подходящие под фильтр, но оставляем видимыми их родителей
        if filter_text:
            for r_id, item in nodes.items():
                c_name = item.text(0).lower()
                c_alias = (item.text(1) or '').lower()
                if filter_text in c_name or filter_text in c_alias:
                    # Совпало — показываем узел и всех его предков
                    cur = item
                    while cur is not None:
                        cur.setHidden(False)
                        cur = cur.parent()
                else:
                    item.setHidden(True)

        self.tree.expandAll()
    def add_group(self):
        """Инъекция текста из фильтра TXT1 в новое окно, если он заполнен."""
        filter_text = self.txt_filter.text().strip()
        dlg = ClassGroupEditDialog(self, db=self.db, group_id=0, initial_name=filter_text)
        if dlg.exec_() == QDialog.Accepted:
            self.load_groups()

    def edit_group(self):
        if not self.current_selected_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_record'))
            return
        dlg = ClassGroupEditDialog(self, db=self.db, group_id=self.current_selected_id)
        if dlg.exec_() == QDialog.Accepted:
            self.load_groups()

    def delete_group(self):
        """Каскадная проверка безопасности на чистоту группы перед удалением."""
        if not self.current_selected_id:
            return

        # Ищем классы в текущей группе и всех её ветках-потомках через рекурсивный CTE-запрос
        sql_check = """
            WITH RECURSIVE sub_categories AS (
                SELECT id FROM class_erp.class_category WHERE id = %s
                UNION ALL
                SELECT cc.id FROM class_erp.class_category cc
                JOIN sub_categories sc ON cc.parent_id = sc.id
            )
            SELECT COUNT(*) FROM class_erp.mozartclasses 
            WHERE category_id IN (SELECT id FROM sub_categories);
        """
        res = self.db.execute_query(sql_check, (self.current_selected_id,))
        classes_count = res[0][0] if res else 0

        if classes_count > 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_clear_group'))
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'), "Удалить группу?") == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM class_erp.class_category WHERE id = %s;", (self.current_selected_id,),
                                  fetch=False)
            self.load_groups()
