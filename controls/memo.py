# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/memo.py

from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Property

from .base_control import BaseControl


class MozartMemo(QPlainTextEdit, BaseControl):
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        BaseControl.__init__(self)
        self._label = ""
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self._is_dirty = self.toPlainText() != self._original_value
        self.value_changed.emit(self.toPlainText())

    def _apply_readonly(self):
        self.setReadOnly(self._is_readonly)

    def set_design_mode(self, design_mode):
        self.setReadOnly(design_mode)
        self.setEnabled(not design_mode)

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

    @Property(bool)
    def is_required(self):
        return self._is_required

    @is_required.setter
    def is_required(self, value):
        self._is_required = value
        if value:
            self.setStyleSheet(self.styleSheet() + "border: 1px solid red;")
        else:
            self.setStyleSheet(self.styleSheet().replace("border: 1px solid red;", ""))

    @Property(bool)
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        self.setReadOnly(value)

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

    def set_value(self, value):
        self.blockSignals(True)
        text = str(value) if value is not None else ""
        self.setPlainText(text)
        self._original_value = text
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        return self.toPlainText()

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self.setPlainText(self._original_value)
        self._is_dirty = False