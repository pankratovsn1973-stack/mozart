# -*- coding: utf-8 -*-
# user_roles/menu_manager.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt

from database import DatabaseService
from lang.local_translator import LocalTranslator
from .dialogs import MenuItemEditDialog


class MenuManager(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_role_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_menu_item)
        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_menu_item)
        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_menu_item)
        self.btn_up = QPushButton(self.translator.tr('btn_up'))
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down = QPushButton(self.translator.tr('btn_down'))
        self.btn_down.clicked.connect(self.move_down)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        layout.addLayout(btn_layout)

        # Дерево меню
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_form'),
            self.translator.tr('field_active')
        ])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 150)
        self.tree.itemDoubleClicked.connect(self.edit_menu_item)
        layout.addWidget(self.tree)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_add.setText(self.translator.tr('btn_add'))
        self.btn_edit.setText(self.translator.tr('btn_edit'))
        self.btn_delete.setText(self.translator.tr('btn_delete'))
        self.btn_up.setText(self.translator.tr('btn_up'))
        self.btn_down.setText(self.translator.tr('btn_down'))
        self.tree.setHeaderLabels([
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_form'),
            self.translator.tr('field_active')
        ])

    def set_role(self, role_id):
        """Устанавливает текущую роль и загружает её меню"""
        self.current_role_id = role_id
        self.load_menu()

    def load_menu(self):
        """Загружает меню для текущей роли из БД"""
        self.tree.clear()

        if not self.current_role_id:
            return

        sql = """
            SELECT id, parentid, cname, calias, iformid, lisactive, isortorder
            FROM meta.menu
            WHERE roleid = %s
            ORDER BY parentid NULLS FIRST, isortorder, id
        """
        rows = self.db.execute_query(sql, (self.current_role_id,))

        if not rows:
            return

        # Получаем названия форм для отображения
        items = {}
        for row in rows:
            item_id, parent_id, cname, calias, iformid, lisactive, sortorder = row

            # Получаем название формы
            form_name = ""
            if iformid:
                form_res = self.db.execute_query(
                    "SELECT cname FROM meta.forms WHERE id = %s", (iformid,)
                )
                if form_res:
                    form_name = form_res[0][0]

            tree_item = QTreeWidgetItem()
            tree_item.setText(0, cname)
            tree_item.setText(1, calias or "")
            tree_item.setText(2, form_name)
            tree_item.setText(3, self.translator.tr('yes') if lisactive else self.translator.tr('no'))
            tree_item.setData(0, Qt.UserRole, item_id)
            tree_item.setData(0, Qt.UserRole + 1, parent_id)
            tree_item.setData(0, Qt.UserRole + 2, sortorder)
            tree_item.setData(0, Qt.UserRole + 3, iformid)

            items[item_id] = tree_item

        # Строим иерархию
        for item_id, tree_item in items.items():
            parent_id = tree_item.data(0, Qt.UserRole + 1)
            if parent_id and parent_id in items:
                items[parent_id].addChild(tree_item)
            else:
                self.tree.addTopLevelItem(tree_item)

        self.tree.expandAll()

    def get_selected_item(self):
        """Возвращает выбранный пункт меню"""
        return self.tree.currentItem()

    def get_selected_id(self):
        item = self.get_selected_item()
        return item.data(0, Qt.UserRole) if item else None

    def add_menu_item(self):
        if not self.current_role_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Сначала выберите роль")
            return

        dlg = MenuItemEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()

            # Определяем максимальный isortorder для корневых или подчинённых
            sql = "SELECT COALESCE(MAX(isortorder), 0) + 10 FROM meta.menu WHERE roleid = %s AND parentid IS NULL"
            res = self.db.execute_query(sql, (self.current_role_id,))
            sortorder = res[0][0] if res else 10

            sql = """
                INSERT INTO meta.menu (roleid, parentid, cname, calias, iformid, lisactive, isortorder)
                VALUES (%s, NULL, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(sql, (self.current_role_id, data["cname"], data["calias"],
                                        data["iformid"], data["lisactive"], sortorder), fetch=False)
            self.load_menu()

    def edit_menu_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_record'))
            return

        sql = "SELECT cname, calias, iformid, copentype, lisactive FROM meta.menu WHERE id = %s"
        row = self.db.execute_query(sql, (item_id,))
        if not row:
            return

        data = {
            "cname": row[0][0],
            "calias": row[0][1],
            "iformid": row[0][2],
            "copentype": row[0][3],
            "lisactive": row[0][4]
        }

        dlg = MenuItemEditDialog(self, data, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """
                UPDATE meta.menu 
                SET cname=%s, calias=%s, iformid=%s, copentype=%s, lisactive=%s
                WHERE id=%s
            """
            self.db.execute_query(sql, (new_data["cname"], new_data["calias"],
                                        new_data["iformid"], new_data["copentype"],
                                        new_data["lisactive"], item_id), fetch=False)
            self.load_menu()

    def delete_menu_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_record'))
            return

        # Проверяем, есть ли дочерние пункты
        sql = "SELECT COUNT(*) FROM meta.menu WHERE parentid = %s"
        res = self.db.execute_query(sql, (item_id,))
        child_count = res[0][0] if res else 0

        if child_count > 0:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Нельзя удалить пункт, у которого есть дочерние элементы")
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_menu_item')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM meta.menu WHERE id=%s", (item_id,), fetch=False)
            self.load_menu()

    def move_up(self):
        """Перемещает пункт меню вверх (уменьшает isortorder)"""
        self._move_item(delta=-10)

    def move_down(self):
        """Перемещает пункт меню вниз (увеличивает isortorder)"""
        self._move_item(delta=10)

    def _move_item(self, delta):
        item = self.get_selected_item()
        if not item:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_record'))
            return

        item_id = item.data(0, Qt.UserRole)
        parent_id = item.data(0, Qt.UserRole + 1)
        current_sort = item.data(0, Qt.UserRole + 2)
        new_sort = current_sort + delta

        if new_sort < 0:
            new_sort = 0

        # Обновляем порядок
        sql = "UPDATE meta.menu SET isortorder = %s WHERE id = %s"
        self.db.execute_query(sql, (new_sort, item_id), fetch=False)

        # Пересортировываем элементы с тем же родителем
        if parent_id:
            sql = """
                UPDATE meta.menu 
                SET isortorder = new_sort
                FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY isortorder) * 10 as new_sort
                    FROM meta.menu
                    WHERE parentid = %s
                ) AS sorted
                WHERE meta.menu.id = sorted.id
            """
            self.db.execute_query(sql, (parent_id,), fetch=False)
        else:
            sql = """
                UPDATE meta.menu 
                SET isortorder = new_sort
                FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY isortorder) * 10 as new_sort
                    FROM meta.menu
                    WHERE roleid = %s AND parentid IS NULL
                ) AS sorted
                WHERE meta.menu.id = sorted.id
            """
            self.db.execute_query(sql, (self.current_role_id,), fetch=False)

        self.load_menu()

        # Выделяем перемещённый элемент
        for i in range(self.tree.topLevelItemCount()):
            child = self.tree.topLevelItem(i)
            if child.data(0, Qt.UserRole) == item_id:
                self.tree.setCurrentItem(child)
                break