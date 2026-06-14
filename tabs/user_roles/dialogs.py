# -*- coding: utf-8 -*-
# user_roles/dialogs.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QCheckBox, QPushButton, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt

from lang.local_translator import LocalTranslator
from database import DatabaseService
from widgets.reference_editor import ReferenceEditor


class UserEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_user_edit'))
        self.data = data or {}
        self.db = db or DatabaseService()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_login = QLineEdit(self.data.get("clogin", ""))
        self.edit_pass = QLineEdit(self.data.get("cpassword_hash", ""))
        self.edit_pass.setEchoMode(QLineEdit.Password)
        self.chk_active = QCheckBox(self.translator.tr('label_active'))
        self.chk_active.setChecked(self.data.get("lactive", True))
        self.edit_person = QLineEdit(str(self.data.get("person_instanceid", "")))

        form.addRow(self.translator.tr('field_login'), self.edit_login)
        form.addRow(self.translator.tr('field_password'), self.edit_pass)
        form.addRow(self.translator.tr('field_person_instance'), self.edit_person)
        form.addRow(self.chk_active)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "clogin": self.edit_login.text().strip(),
            "cpassword_hash": self.edit_pass.text(),
            "lactive": self.chk_active.isChecked(),
            "person_instanceid": self.edit_person.text().strip() or None
        }


class RoleEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_role_edit'))
        self.data = data or {}
        self.db = db or DatabaseService()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))

        self.ref_parent = ReferenceEditor(
            table_name='auth.roles',
            display_field='cname',
            db=self.db
        )
        if self.data.get("parentid"):
            res = self.db.execute_query(
                "SELECT cname FROM auth.roles WHERE id = %s",
                (self.data["parentid"],)
            )
            if res:
                self.ref_parent.set_value(self.data["parentid"], res[0][0])

        self.chk_interface = QCheckBox(self.translator.tr('label_interface_role'))
        self.chk_interface.setChecked(self.data.get("lisinterface", False))
        self.edit_path = QLineEdit(self.data.get("cinterface_path", ""))
        self.edit_comment = QLineEdit(self.data.get("mcomment", ""))

        form.addRow(self.translator.tr('field_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.translator.tr('field_parent_role'), self.ref_parent)
        form.addRow(self.chk_interface)
        form.addRow(self.translator.tr('field_interface_path'), self.edit_path)
        form.addRow(self.translator.tr('field_comment'), self.edit_comment)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "parentid": self.ref_parent.get_value(),
            "lisinterface": self.chk_interface.isChecked(),
            "cinterface_path": self.edit_path.text(),
            "mcomment": self.edit_comment.text()
        }


class ContextEditDialog(QDialog):
    def __init__(self, parent=None, users=None, roles=None, bus=None,
                 current_userid=None, current_roleid=None, current_buid=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_context_assign'))

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_user = QComboBox()
        for uid, ulogin in users or []:
            self.combo_user.addItem(f"{ulogin} ({uid})", uid)

        self.combo_role = QComboBox()
        for rid, rname in roles or []:
            self.combo_role.addItem(f"{rname} ({rid})", rid)

        self.combo_bu = QComboBox()
        for bid, bname in bus or []:
            self.combo_bu.addItem(f"{bname} ({bid})", bid)

        form.addRow(self.translator.tr('field_user'), self.combo_user)
        form.addRow(self.translator.tr('field_role'), self.combo_role)
        form.addRow(self.translator.tr('field_balance_unit'), self.combo_bu)
        layout.addLayout(form)

        # Устанавливаем текущие значения, если переданы
        if current_userid:
            idx = self.combo_user.findData(current_userid)
            if idx >= 0:
                self.combo_user.setCurrentIndex(idx)

        if current_roleid:
            idx = self.combo_role.findData(current_roleid)
            if idx >= 0:
                self.combo_role.setCurrentIndex(idx)

        if current_buid:
            idx = self.combo_bu.findData(current_buid)
            if idx >= 0:
                self.combo_bu.setCurrentIndex(idx)

        btns = QHBoxLayout()
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "userid": self.combo_user.currentData(),
            "roleid": self.combo_role.currentData(),
            "balanceunitid": self.combo_bu.currentData()
        }


class MenuItemEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_menu_item_edit'))
        self.data = data or {}
        self.db = db or DatabaseService()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))

        # Выбор формы
        self.ref_form = ReferenceEditor(
            table_name='meta.forms',
            display_field='cname',
            db=self.db
        )
        if self.data.get("iformid"):
            res = self.db.execute_query(
                "SELECT cname FROM meta.forms WHERE id = %s",
                (self.data["iformid"],)
            )
            if res:
                self.ref_form.set_value(self.data["iformid"], res[0][0])

        # Тип открытия
        self.combo_open_type = QComboBox()
        self.combo_open_type.addItem(self.translator.tr('open_type_main'), 'main')
        self.combo_open_type.addItem(self.translator.tr('open_type_tab'), 'tab')
        self.combo_open_type.addItem(self.translator.tr('open_type_dialog'), 'dialog')
        current_type = self.data.get("copentype", "main")
        idx = self.combo_open_type.findData(current_type)
        if idx >= 0:
            self.combo_open_type.setCurrentIndex(idx)

        # Активен
        self.chk_active = QCheckBox(self.translator.tr('label_active'))
        self.chk_active.setChecked(self.data.get("lisactive", True))

        form.addRow(self.translator.tr('field_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.translator.tr('field_form'), self.ref_form)
        form.addRow(self.translator.tr('field_open_type'), self.combo_open_type)
        form.addRow(self.chk_active)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "iformid": self.ref_form.get_value(),
            "copentype": self.combo_open_type.currentData(),
            "lisactive": self.chk_active.isChecked()
        }