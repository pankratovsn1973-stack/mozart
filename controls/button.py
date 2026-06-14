# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/button.py

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Property, Signal

from .base_control import BaseControl


class MozartButton(QPushButton, BaseControl):
    value_changed = Signal(bool)

    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        BaseControl.__init__(self)
        self._label = "Кнопка"
        self.setText(self._label)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self._is_dirty = True
        self.value_changed.emit(True)

    def _apply_readonly(self):
        self.setEnabled(not self._is_readonly)

    def set_design_mode(self, design_mode):
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

    @Property(bool)
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        self.setEnabled(not value)

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        props = BaseControl.properties.fget(self)
        props.update({'label': self.text()})
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'label' in value:
            self.setText(value['label'])
            self._label = value['label']

    def set_value(self, value):
        self.blockSignals(True)
        self._original_value = value
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        return None

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self._is_dirty = False