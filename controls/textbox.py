# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/textbox.py

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Property, Signal, Qt

from .base_control import BaseControl


class MozartTextBox(QLineEdit, BaseControl):
    value_changed = Signal(str)

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        BaseControl.__init__(self)
        self._label = ""
        self._original_value = ""
        self._design_mode = False
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self._is_dirty = self.text() != self._original_value
        self.value_changed.emit(self.text())

    def _apply_readonly(self):
        self.setReadOnly(self._is_readonly)

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        self.setReadOnly(design_mode)

        if design_mode:
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        else:
            self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

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
            self.setStyleSheet(self.styleSheet().replace(
                "border: 1px solid red;") if "border: 1px solid red;" in self.styleSheet() else self.styleSheet())

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
        props = BaseControl.properties.fget(self)
        props.update({'label': self.placeholderText() or self._label})
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'label' in value:
            self.setPlaceholderText(value['label'])
            self._label = value['label']

    def set_value(self, value):
        self.blockSignals(True)
        self.setText(str(value) if value is not None else "")
        self._original_value = self.text()
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        return self.text()

    def is_dirty(self):
        return self.text() != self._original_value

    def reset(self):
        self.setText(self._original_value)
        self._is_dirty = False
