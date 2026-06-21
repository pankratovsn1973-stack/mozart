# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/container.py

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QWidget
from PySide6.QtCore import Property

from .base_control import BaseControl


class MozartContainer(QGroupBox, BaseControl):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        BaseControl.__init__(self)
        self.setTitle("Группа элементов")
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self._layout)

    def set_design_mode(self, design_mode):
        # КРИТИЧЕСКИЙ ФИКС: QWidget теперь импортирован корректно
        for child in self.findChildren(QWidget):
            if hasattr(child, 'set_design_mode'):
                child.set_design_mode(design_mode)

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

    def add_control(self, control):
        self._layout.addWidget(control)

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        return BaseControl.properties.fget(self)

    @properties.setter
    def properties(self, value):
        if value:
            BaseControl.properties.fset(self, value)

    def set_value(self, value):
        pass

    def get_value(self):
        return None

    def is_dirty(self):
        return False

    def reset(self):
        pass
