# tabs/users_roles/user_edit_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QMessageBox
from lang.local_translator import LocalTranslator
from database import DatabaseService

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
            "cpassword_hash": self.edit_pass.text(),   # открытый пароль, потом захешируем
            "lactive": self.chk_active.isChecked(),
            "person_instanceid": self.edit_person.text().strip() or None
        }