# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/datebox.py

from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import Property, QDate

from .base_control import BaseControl


class MozartDateBox(QDateEdit, BaseControl):
    def __init__(self, parent=None):
        QDateEdit.__init__(self, parent)
        BaseControl.__init__(self)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy")
        self.dateChanged.connect(self._on_date_changed)

    def _on_date_changed(self, date):
        self._is_dirty = self.date() != self._original_value
        self.value_changed.emit(self.get_value())

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

    @Property(str)
    def date_format(self):
        return self.displayFormat()

    @date_format.setter
    def date_format(self, value):
        self.setDisplayFormat(value)

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        props = BaseControl.properties.fget(self)
        props.update({'date_format': self.displayFormat()})
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'date_format' in value:
            self.setDisplayFormat(value['date_format'])

    def set_value(self, value):
        self.blockSignals(True)
        if value:
            qdate = QDate.fromString(value, "yyyy-MM-dd")
            if qdate.isValid():
                self.setDate(qdate)
                self._original_value = self.date()
            else:
                self.clear()
                self._original_value = None
        else:
            self.clear()
            self._original_value = None
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        return self.date().toString("yyyy-MM-dd") if self.date().isValid() else None

    def is_dirty(self):
        return self.date() != self._original_value

    def reset(self):
        if self._original_value:
            self.setDate(self._original_value)
        else:
            self.clear()
        self._is_dirty = False