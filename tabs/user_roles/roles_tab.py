# -*- coding: utf-8 -*-
# user_roles/roles_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMessageBox
from PySide6.QtCore import Qt, Signal

from database import DatabaseService
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator
from .dialogs import RoleEditDialog


class RolesTab(QWidget):
    role_selected = Signal(object)
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_role_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.crud = CrudButtons(self)
        layout.addWidget(self.crud)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_interface'),
            self.translator.tr('field_interface_path')
        ])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 120)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.edit_role)
        layout.addWidget(self.tree)

        self.crud.add_clicked.connect(self.add_role)
        self.crud.edit_clicked.connect(self.edit_role)
        self.crud.delete_clicked.connect(self.delete_role)

        self.retranslate_ui()
        self.load_data()

    def retranslate_ui(self):
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_interface'),
            self.translator.tr('field_interface_path')
        ])
        self.crud.retranslate_ui()

    def load_data(self):
        sql = "SELECT id, parentid, level, data FROM get_hierarchy_iterative(%s, %s, %s)"
        rows = self.db.execute_query(sql, ('auth.roles', 'id', 'parentid'))

        self.tree.clear()
        items = {}

        for row in rows:
            node_id, parent_id, level, data = row
            name = data.get('cname', '')
            alias = data.get('calias', '')
            is_interface = data.get('lisinterface', False)
            interface_path = data.get('cinterface_path', '')

            item = QTreeWidgetItem()
            item.setText(0, str(node_id))
            item.setText(1, name)
            item.setText(2, alias)
            item.setText(3, "Да" if is_interface else "Нет")
            item.setText(4, interface_path or "")
            item.setData(0, Qt.UserRole, node_id)
            items[node_id] = item

            if parent_id is None:
                self.tree.addTopLevelItem(item)
            else:
                if parent_id in items:
                    items[parent_id].addChild(item)
                else:
                    self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def get_selected_id(self):
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def on_item_clicked(self, item, column):
        """Сигнал при клике на роль — сохраняем ID и испускаем сигнал"""
        self.current_role_id = item.data(0, Qt.UserRole)
        if hasattr(self, 'role_selected'):
            self.role_selected.emit(self.current_role_id)

    def add_role(self):
        dlg = RoleEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO auth.roles (cname, calias, parentid, lisinterface, cinterface_path, mcomment)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            self.db.execute_query(sql, (data["cname"], data["calias"], data["parentid"],
                                        data["lisinterface"], data["cinterface_path"], data["mcomment"]), fetch=False)
            self.load_data()

    def edit_role(self):
        role_id = self.get_selected_id()
        if not role_id:
            self.show_warning(self.translator.tr('warning_select_role'))
            return

        sql = "SELECT cname, calias, parentid, lisinterface, cinterface_path, mcomment FROM auth.roles WHERE id=%s"
        row = self.db.execute_query(sql, (role_id,))
        if not row:
            return

        data = {
            "cname": row[0][0],
            "calias": row[0][1],
            "parentid": row[0][2],
            "lisinterface": row[0][3],
            "cinterface_path": row[0][4],
            "mcomment": row[0][5]
        }

        dlg = RoleEditDialog(self, data, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """UPDATE auth.roles SET cname=%s, calias=%s, parentid=%s, lisinterface=%s, 
                        cinterface_path=%s, mcomment=%s WHERE id=%s"""
            self.db.execute_query(sql, (new_data["cname"], new_data["calias"], new_data["parentid"],
                                        new_data["lisinterface"], new_data["cinterface_path"],
                                        new_data["mcomment"], role_id), fetch=False)
            self.load_data()

    def delete_role(self):
        role_id = self.get_selected_id()
        if not role_id:
            self.show_warning(self.translator.tr('warning_select_role'))
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_role')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM auth.roles WHERE id=%s", (role_id,), fetch=False)
            self.load_data()

    def show_warning(self, message):
        QMessageBox.warning(self, self.translator.tr('warning'), message)