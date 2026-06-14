# -*- coding: utf-8 -*-
# user_roles/context_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt

from database import DatabaseService
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator
from .dialogs import ContextEditDialog


class ContextTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.crud = CrudButtons(self, with_add=True, with_edit=True, with_delete=True)
        layout.addWidget(self.crud)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.crud.add_clicked.connect(self.add_context)
        self.crud.edit_clicked.connect(self.edit_context)
        self.crud.delete_clicked.connect(self.delete_context)

        self.retranslate_ui()
        self.load_data()

    def retranslate_ui(self):
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_user'),
            self.translator.tr('field_role'),
            self.translator.tr('field_balance_unit')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.crud.retranslate_ui()

    def load_data(self):
        sql = """SELECT urc.id, u.clogin, r.cname, bu.cname
                 FROM auth.userrolecontext urc
                 JOIN auth.users u ON urc.userid = u.id
                 JOIN auth.roles r ON urc.roleid = r.id
                 JOIN auth.balanceunits bu ON urc.balanceunitid = bu.id
                 ORDER BY urc.id"""
        rows = self.db.execute_query(sql)
        self.table.setRowCount(0)
        for row in rows:
            pos = self.table.rowCount()
            self.table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
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

    def get_users_list(self):
        return self.db.execute_query("SELECT id, clogin FROM auth.users ORDER BY clogin")

    def get_roles_list(self):
        return self.db.execute_query("SELECT id, cname FROM auth.roles ORDER BY cname")

    def get_bus_list(self):
        return self.db.execute_query("SELECT id, cname FROM auth.balanceunits ORDER BY cname")

    def add_context(self):
        users = self.get_users_list()
        roles = self.get_roles_list()
        bus = self.get_bus_list()

        if not users or not roles or not bus:
            self.show_warning(self.translator.tr('warning_context_required'))
            return

        dlg = ContextEditDialog(self, users, roles, bus)
        if dlg.exec_():
            data = dlg.get_data()
            try:
                sql = """INSERT INTO auth.userrolecontext (userid, roleid, balanceunitid)
                         VALUES (%s, %s, %s)"""
                self.db.execute_query(sql, (data["userid"], data["roleid"], data["balanceunitid"]), fetch=False)
                self.load_data()
            except Exception as e:
                if "already has an interface role" in str(e):
                    self.show_error("Нельзя назначить пользователю две интерфейсные роли в одной балансовой единице")
                else:
                    self.show_error(f"Ошибка: {str(e)}")

    def edit_context(self):
        ctx_id = self.get_selected_id()
        if not ctx_id:
            self.show_warning(self.translator.tr('warning_select_context'))
            return

        sql = "SELECT userid, roleid, balanceunitid FROM auth.userrolecontext WHERE id = %s"
        row = self.db.execute_query(sql, (ctx_id,))
        if not row:
            return

        current_userid, current_roleid, current_buid = row[0]

        users = self.get_users_list()
        roles = self.get_roles_list()
        bus = self.get_bus_list()

        dlg = ContextEditDialog(self, users, roles, bus,
                                current_userid, current_roleid, current_buid)
        if dlg.exec_():
            data = dlg.get_data()

            # Проверяем, что хоть что-то изменилось
            if (data["userid"] == current_userid and
                    data["roleid"] == current_roleid and
                    data["balanceunitid"] == current_buid):
                return

            try:
                sql = """UPDATE auth.userrolecontext
                         SET userid=%s, roleid=%s, balanceunitid=%s
                         WHERE id=%s"""
                self.db.execute_query(sql, (data["userid"], data["roleid"],
                                            data["balanceunitid"], ctx_id), fetch=False)
                self.load_data()
            except Exception as e:
                if "already has an interface role" in str(e):
                    self.show_error("Нельзя назначить пользователю две интерфейсные роли в одной балансовой единице")
                else:
                    self.show_error(f"Ошибка: {str(e)}")

    def delete_context(self):
        ctx_id = self.get_selected_id()
        if not ctx_id:
            self.show_warning(self.translator.tr('warning_select_context'))
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_context')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM auth.userrolecontext WHERE id=%s", (ctx_id,), fetch=False)
            self.load_data()

    def show_warning(self, message):
        QMessageBox.warning(self, self.translator.tr('warning'), message)

    def show_error(self, message):
        QMessageBox.critical(self, self.translator.tr('error'), message)