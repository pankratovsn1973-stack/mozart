# Полный путь: dialogs/class_group_edit_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTreeWidget,QTextEdit,
    QTreeWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator


class ClassGroupEditDialog(QDialog):
    """Окно добавления/редактирования одной группы классификатора."""

    def __init__(self, parent=None, db: DatabaseService = None, group_id: int = 0, initial_name: str = ""):
        super().__init__(parent)
        self.db = db
        self.group_id = group_id
        self.initial_name = initial_name
        self.translator = LocalTranslator()
        self.selected_parent_id = None

        self.setWindowTitle(self.translator.tr('title_group_edit'))
        self.resize(500, 450)
        self.setup_ui()
        self.load_parent_tree()

        if self.group_id > 0:
            self.load_group_data()

    def setup_ui(self):
        """Настройка интерфейса диалога с добавлением поля дескрипции группы."""
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Системное имя группы
        self.edit_cname = QLineEdit()
        if self.group_id == 0 and self.initial_name:
            self.edit_cname.setText(self.initial_name)
        form.addRow(self.translator.tr('field_name') + ":", self.edit_cname)

        # Системный алиас
        self.edit_calias = QLineEdit()
        form.addRow(self.translator.tr('field_alias') + ":", self.edit_calias)

        # 🚀 ДОБАВЛЕНО: Поле описания (дескрипции) группы
        self.edit_comment = QTextEdit()
        self.edit_comment.setPlaceholderText("Укажите назначение этой группы классов...")
        self.edit_comment.setMaximumHeight(80)
        form.addRow(self.translator.tr('field_description') + ":", self.edit_comment)

        layout.addLayout(form)

        # Выбор родителя
        layout.addWidget(QLabel(f"<b>{self.translator.tr('field_parent')}:</b>"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([self.translator.tr('field_name')])
        self.tree.itemChanged.connect(self.on_item_checked)
        layout.addWidget(self.tree)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton(self.translator.tr('btn_clear_parent'))
        self.btn_clear.clicked.connect(self.clear_parent_selection)
        btn_layout.addWidget(self.btn_clear)

        btn_layout.addStretch()
        self.btn_ok = QPushButton(self.translator.tr('btn_ok'))
        self.btn_ok.clicked.connect(self.save_data)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def clear_parent_selection(self):
        """Сбрасывает все галочки, делая группу корневой."""
        self.tree.blockSignals(True)
        self.selected_parent_id = None
        for i in range(self.tree.topLevelItemCount()):
            self._uncheck_recursive(self.tree.topLevelItem(i))
        self.tree.blockSignals(False)

    def _uncheck_recursive(self, item: QTreeWidgetItem):
        item.setCheckState(0, Qt.CheckState.Unchecked)
        for i in range(item.childCount()):
            self._uncheck_recursive(item.child(i))

    def on_item_checked(self, item: QTreeWidgetItem, column: int):
        """Гарантирует триггер только ОДНОГО чекбокса в иерархии."""
        self.tree.blockSignals(True)
        if item.checkState(0) == Qt.CheckState.Checked:
            self.selected_parent_id = item.data(0, Qt.UserRole)
            # Снимаем отметки со всех остальных
            for i in range(self.tree.topLevelItemCount()):
                self._clear_other_checks(self.tree.topLevelItem(i), item)
        else:
            if self.selected_parent_id == item.data(0, Qt.UserRole):
                self.selected_parent_id = None
        self.tree.blockSignals(False)

    def _clear_other_checks(self, current_item: QTreeWidgetItem, target_item: QTreeWidgetItem):
        if current_item != target_item:
            current_item.setCheckState(0, Qt.CheckState.Unchecked)
        for i in range(current_item.childCount()):
            self._clear_other_checks(current_item.child(i), target_item)

    def load_parent_tree(self):
        """Строит дерево потенциальных родителей из базы данных."""
        self.tree.blockSignals(True)
        self.tree.clear()
        # Выгребаем рекурсивную иерархию категорий из СУБД
        sql = "SELECT id, parent_id, c_name FROM class_erp.class_category ORDER BY i_sortorder, id;"
        rows = self.db.execute_query(sql) or []
        nodes = {}
        for r_id, p_id, c_name in rows:
            if r_id == self.group_id:
                continue  # Нельзя выбрать самого себя родителем
            item = QTreeWidgetItem()
            item.setText(0, c_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setData(0, Qt.UserRole, r_id)
            nodes[r_id] = item
            if p_id and p_id in nodes:
                nodes[p_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        self.tree.blockSignals(False)

    def load_group_data(self):
        """Загрузка полей существующей группы, включая дескрипцию (mcomment)."""
        sql = "SELECT c_name, c_alias, parent_id, mcomment FROM class_erp.class_category WHERE id = %s;"
        res = self.db.execute_query(sql, (self.group_id,))
        if res:
            # Извлекаем данные из первой строки ответа Постгреса
            db_record = res[0] if isinstance(res[0], (list, tuple)) else res

            name = db_record[0]
            alias = db_record[1]
            p_id = db_record[2]
            comment = db_record[3] if len(db_record) > 3 else ""

            self.edit_cname.setText(str(name or ""))
            self.edit_calias.setText(str(alias or ""))
            self.edit_comment.setPlainText(str(comment or ""))

            self.selected_parent_id = p_id
            if p_id:
                self._set_check_recursive(self.tree.invisibleRootItem(), p_id)

    def _set_check_recursive(self, root: QTreeWidgetItem, target_id: int):
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole) == target_id:
                child.setCheckState(0, Qt.CheckState.Checked)
                break
            self._set_check_recursive(child, target_id)

    def save_data(self):
        """Запись изменений, включая описание (mcomment), в PostgreSQL."""
        name = self.edit_cname.text().strip()
        alias = self.edit_calias.text().strip()
        comment = self.edit_comment.toPlainText().strip()

        if not name or not alias:
            QMessageBox.warning(self, self.translator.tr('warning'), "Заполните имя и алиас!")
            return

        if self.group_id == 0:
            sql = "INSERT INTO class_erp.class_category (c_name, c_alias, parent_id, mcomment) VALUES (%s, %s, %s, %s);"
            self.db.execute_query(sql, (name, alias, self.selected_parent_id, comment), fetch=False)
        else:
            sql = "UPDATE class_erp.class_category SET c_name=%s, c_alias=%s, parent_id=%s, mcomment=%s WHERE id=%s;"
            self.db.execute_query(sql, (name, alias, self.selected_parent_id, comment, self.group_id), fetch=False)

        self.accept()
