# mozart_import/wizards/wizard_dialogs.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDialogButtonBox
from lang.local_translator import LocalTranslator


class NewFieldDialog(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('new_field_dialog_title'))

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        form.addRow(self.translator.tr('field_name_latin'), self.name_edit)

        self.alias_edit = QLineEdit()
        form.addRow(self.translator.tr('field_alias'), self.alias_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["C", "N", "I", "D", "T", "L", "M", "R"])
        form.addRow(self.translator.tr('mozart_type'), self.type_combo)

        self.length_edit = QSpinBox()
        self.length_edit.setRange(1, 10000)
        self.length_edit.setValue(255)
        form.addRow(self.translator.tr('length_for_string'), self.length_edit)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        self.name_edit.textChanged.connect(lambda: self.name_edit.setText(self.name_edit.text()[:63]))
        self.alias_edit.textChanged.connect(lambda: self.alias_edit.setText(self.alias_edit.text()[:50]))
        layout.addWidget(btn_box)

    def get_data(self):
        return {
            'cfieldname': self.name_edit.text(),
            'calias': self.alias_edit.text() or self.name_edit.text(),
            'cfieldtype': self.type_combo.currentText(),
            'nlength': self.length_edit.value()
        }


class NewEntityDialog(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('create_entity_dialog_title'))

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        form.addRow(self.translator.tr('entity_name_cname'), self.name_edit)

        self.alias_edit = QLineEdit()
        form.addRow(self.translator.tr('entity_alias_calias'), self.alias_edit)

        self.class_combo = QComboBox()
        classes = self.db.execute_query("SELECT id, cname FROM meta.entity_classes ORDER BY cname")
        for cid, cname in classes:
            self.class_combo.addItem(cname, cid)
        form.addRow(self.translator.tr('entity_class'), self.class_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_data(self):
        return {
            'cname': self.name_edit.text(),
            'calias': self.alias_edit.text(),
            'class_id': self.class_combo.currentData()
        }