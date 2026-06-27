# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/reference_base.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Property, Signal
from .base_control import BaseControl


class MozartReferenceBase(QWidget, BaseControl):
    """Базовый класс ERP-компонента Ссылка, изолирующий метаданные и свойства."""
    value_changed = Signal(object)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)

        self._binding_field = ""
        self._entity_alias = ""
        self._display_field = "cname"
        self._selector_form = ""

        self._current_id = None
        self._display_value = ""
        self._db = None
        self._label = "Ссылка:"
        self._design_mode = False

    @Property(str)
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = str(value)
        if hasattr(self, '_update_label'):
            self._update_label()

    @Property(str)
    def binding_field(self):
        return self._binding_field

    @binding_field.setter
    def binding_field(self, value):
        self._binding_field = str(value)

    @Property(str)
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = str(value)
        if self._design_mode and hasattr(self, 'edit_design') and self.edit_design:
            self.edit_design.setText(f"Справочник: {self._entity_alias}" if self._entity_alias else "Не выбрано")

    @Property(str)
    def display_field(self):
        return self._display_field

    @display_field.setter
    def display_field(self, value):
        self._display_field = str(value)

    @Property(str)
    def selector_form(self):
        return self._selector_form

    @selector_form.setter
    def selector_form(self, value):
        self._selector_form = str(value)

    @Property(bool)
    def is_required(self):
        return getattr(self, '_is_required', False)

    @Property(bool)
    def is_readonly(self):
        return getattr(self, '_is_readonly', False)

    def set_db(self, db):
        self._db = db

    @property
    def properties(self):
        return {
            'label': self._label, 'binding_field': self._binding_field,
            'entity_alias': self._entity_alias, 'display_field': self._display_field,
            'selector_form': self._selector_form, 'is_required': getattr(self, '_is_required', False),
            'is_readonly': getattr(self, '_is_readonly', False),
        }

    @properties.setter
    def properties(self, value):
        if not value:
            return
        self._binding_field = value.get('binding_field', '')
        self._entity_alias = value.get('entity_alias', '')
        self._display_field = value.get('display_field', 'cname')
        self._selector_form = value.get('selector_form', '')
        if hasattr(self, 'set_required_state'):
            self.set_required_state(value.get('is_required', False))
        if hasattr(self, 'set_readonly_state'):
            self.set_readonly_state(value.get('is_readonly', False))
