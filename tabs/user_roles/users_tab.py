# -*- coding: utf-8 -*-
# user_roles/users_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt

from database import DatabaseService
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator
from .dialogs import UserEditDialog


class UsersTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.crud = CrudButtons(self)
        layout.addWidget(self.crud)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.edit_user)
        layout.addWidget(self.table)

        self.crud.add_clicked.connect(self.add_user)
        self.crud.edit_clicked.connect(self.edit_user)
        self.crud.delete_clicked.connect(self.delete_user)

        self.retranslate_ui()
        self.load_data()

    def retranslate_ui(self):
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_login'),
            self.translator.tr('field_active'),
            self.translator.tr('field_person_instance')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.crud.retranslate_ui()

    def load_data(self):
        sql = "SELECT id, clogin, lactive, person_instanceid FROM auth.users ORDER BY id"
        rows = self.db.execute_query(sql)
        self.table.setRowCount(0)
        for row in rows:
            pos = self.table.rowCount()
            self.table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else "")
                if col == 0:
                    item.setData(Qt.UserRole, val)
                self.table.setItem(pos, col, item)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None

    def add_user(self):
        dlg = UserEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO auth.users (clogin, cpassword_hash, lactive, person_instanceid)
                     VALUES (%s, %s, %s, %s)"""
            self.db.execute_query(sql, (data["clogin"], data["cpassword_hash"],
                                        data["lactive"], data["person_instanceid"]), fetch=False)
            self.load_data()

    def edit_user(self):
        user_id = self.get_selected_id()
        if not user_id:
            self.show_warning(self.translator.tr('warning_select_user'))
            return

        sql = "SELECT clogin, cpassword_hash, lactive, person_instanceid FROM auth.users WHERE id=%s"
        row = self.db.execute_query(sql, (user_id,))
        if not row:
            return

        data = {
            "clogin": row[0][0],
            "cpassword_hash": row[0][1],
            "lactive": row[0][2],
            "person_instanceid": row[0][3]
        }

        dlg = UserEditDialog(self, data, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """UPDATE auth.users SET clogin=%s, cpassword_hash=%s, lactive=%s, person_instanceid=%s 
                     WHERE id=%s"""
            self.db.execute_query(sql, (new_data["clogin"], new_data["cpassword_hash"],
                                        new_data["lactive"], new_data["person_instanceid"], user_id), fetch=False)
            self.load_data()

    def delete_user(self):
        user_id = self.get_selected_id()
        if not user_id:
            self.show_warning(self.translator.tr('warning_select_user'))
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_user')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM auth.users WHERE id=%s", (user_id,), fetch=False)
            self.load_data()

    def show_warning(self, message):
        QMessageBox.warning(self, self.translator.tr('warning'), message)