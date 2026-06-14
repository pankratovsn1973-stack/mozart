# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/reference.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Property, Signal

from .base_control import BaseControl


class MozartReference(QWidget, BaseControl):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)
        self._display_field = "cname"
        self._selector_form = ""
        self._current_id = None
        self._display_value = ""
        self._db = None
        self._label = ""
        self._design_mode = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setReadOnly(True)
        layout.addWidget(self.edit)
        self.btn_select = QPushButton("📁")
        self.btn_select.setFixedWidth(30)
        self.btn_select.clicked.connect(self.select_value)
        layout.addWidget(self.btn_select)
        self.btn_clear = QPushButton("✖")
        self.btn_clear.setFixedWidth(30)
        self.btn_clear.clicked.connect(self.clear_value)
        layout.addWidget(self.btn_clear)

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        self.btn_select.setEnabled(not design_mode)
        self.btn_clear.setEnabled(not design_mode)
        self.edit.setReadOnly(True)

    @Property(str)
    def binding_field(self):
        return self._binding_field

    @binding_field.setter
    def binding_field(self, value):
        self._binding_field = value

    @Property(str)
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value

    @Property(str)
    def display_field(self):
        return self._display_field

    @display_field.setter
    def display_field(self, value):
        self._display_field = value

    @Property(str)
    def selector_form(self):
        return self._selector_form

    @selector_form.setter
    def selector_form(self, value):
        self._selector_form = value

    @Property(bool)
    def is_required(self):
        return self._is_required

    @is_required.setter
    def is_required(self, value):
        self._is_required = value
        if value:
            self.edit.setStyleSheet("border: 1px solid red;")
        else:
            self.edit.setStyleSheet("")

    @Property(bool)
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        if not self._design_mode:
            self.edit.setReadOnly(value)
            self.btn_select.setEnabled(not value)
            self.btn_clear.setEnabled(not value)

    def set_db(self, db):
        self._db = db

    def set_value(self, instance_id, display_value=None):
        self._current_id = instance_id
        if display_value is not None:
            self._display_value = display_value
        elif instance_id and self._db and self._entity_alias and self._display_field:
            res = self._db.execute_query(
                f"SELECT {self._display_field} FROM data.entity_instances i "
                f"JOIN data.entity_versions v ON i.id = v.instanceid "
                f"JOIN ext.ext_{self._entity_alias} e ON v.id = e.versionid "
                f"WHERE i.id = %s AND v.cversionstatus = 'Active'",
                (instance_id,)
            )
            if res:
                self._display_value = str(res[0][0]) if res[0][0] else ""
            else:
                self._display_value = ""
        else:
            self._display_value = ""
        self.edit.setText(self._display_value)
        self._original_value = instance_id
        self._is_dirty = False
        self.value_changed.emit(instance_id)

    def get_value(self):
        return self._current_id

    def is_dirty(self):
        return self._current_id != self._original_value

    def reset(self):
        self.set_value(self._original_value)

    def select_value(self):
        if self._is_readonly or self._design_mode:
            return
        if not self._entity_alias:
            QMessageBox.warning(self, "Ошибка", "Не указан entity_alias для Reference")
            return
        QMessageBox.information(self, "Выбор", f"Открыть форму выбора для {self._entity_alias}")

    def clear_value(self):
        self.set_value(None, "")

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        return {
            'binding_field': self._binding_field,
            'entity_alias': self._entity_alias,
            'is_required': self._is_required,
            'is_readonly': self._is_readonly,
            'label': self._label,
            'display_field': self._display_field,
            'selector_form': self._selector_form,
        }

    @properties.setter
    def properties(self, value):
        if not value:
            return
        self._binding_field = value.get('binding_field', '')
        self._entity_alias = value.get('entity_alias', '')
        self._is_required = value.get('is_required', False)
        self._is_readonly = value.get('is_readonly', False)
        if 'label' in value:
            self._label = value['label']
        if 'display_field' in value:
            self._display_field = value['display_field']
        if 'selector_form' in value:
            self._selector_form = value['selector_form']