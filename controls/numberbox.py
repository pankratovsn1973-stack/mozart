# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/numberbox.py

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Property, Qt, QLocale
from PySide6.QtGui import QDoubleValidator

from .base_control import BaseControl


class MozartNumberBox(QLineEdit, BaseControl):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        BaseControl.__init__(self)
        self._min_value = 0.0
        self._max_value = 999999999.0
        self._decimal_places = 2
        self._label = ""
        self.setAlignment(Qt.AlignRight)
        self._update_validator()
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self._is_dirty = self.text() != self._original_value
        self.value_changed.emit(self.get_value())

    def _apply_readonly(self):
        self.setReadOnly(self._is_readonly)

    def _update_validator(self):
        validator = QDoubleValidator(self._min_value, self._max_value, self._decimal_places, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        validator.setLocale(QLocale(QLocale.English))
        self.setValidator(validator)

    def set_design_mode(self, design_mode):
        self.setReadOnly(design_mode)
        self.setEnabled(not design_mode)

    @Property(float)
    def min_value(self):
        return self._min_value

    @min_value.setter
    def min_value(self, value):
        self._min_value = value
        self._update_validator()

    @Property(float)
    def max_value(self):
        return self._max_value

    @max_value.setter
    def max_value(self, value):
        self._max_value = value
        self._update_validator()

    @Property(int)
    def decimal_places(self):
        return self._decimal_places

    @decimal_places.setter
    def decimal_places(self, value):
        self._decimal_places = value
        self._update_validator()

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
        props = BaseControl.properties.fget(self)
        props.update({
            'label': self.placeholderText() or self._label,
            'min_value': self._min_value,
            'max_value': self._max_value,
            'decimal_places': self._decimal_places,
        })
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'label' in value:
            self.setPlaceholderText(value['label'])
            self._label = value['label']
        if 'min_value' in value:
            self._min_value = value['min_value']
        if 'max_value' in value:
            self._max_value = value['max_value']
        if 'decimal_places' in value:
            self._decimal_places = value['decimal_places']
        self._update_validator()

    def set_value(self, value):
        self.blockSignals(True)
        if value is not None:
            try:
                self.setText(f"{float(value):.{self._decimal_places}f}")
            except:
                self.setText("")
        else:
            self.setText("")
        self._original_value = self.text()
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        try:
            return float(self.text()) if self.text() else None
        except ValueError:
            return None

    def is_dirty(self):
        return self.text() != self._original_value

    def reset(self):
        self.setText(self._original_value)
        self._is_dirty = False