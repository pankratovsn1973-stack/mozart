# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/tab_container.py

import json
from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Property

from .base_control import BaseControl


class MozartTabContainer(QTabWidget, BaseControl):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        BaseControl.__init__(self)
        self._tabs_json = "[]"

    def set_design_mode(self, design_mode):
        for i in range(self.count()):
            widget = self.widget(i)
            if hasattr(widget, 'set_design_mode'):
                widget.set_design_mode(design_mode)

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

    @Property(str)
    def tabs_json(self):
        return self._tabs_json

    @tabs_json.setter
    def tabs_json(self, value):
        self._tabs_json = value
        self._load_tabs()

    def _load_tabs(self):
        for i in range(self.count() - 1, -1, -1):
            widget = self.widget(i)
            self.removeTab(i)
            if widget:
                widget.deleteLater()
        try:
            tabs = json.loads(self._tabs_json)
            for tab in tabs:
                tab_label = tab.get('label', 'Вкладка')
                tab_widget = QWidget()
                tab_layout = QVBoxLayout(tab_widget)
                self.addTab(tab_widget, tab_label)
                setattr(tab_widget, '_tab_layout', tab_layout)
        except:
            pass

    def get_tab_layout(self, index):
        widget = self.widget(index)
        if widget and hasattr(widget, '_tab_layout'):
            return widget._tab_layout
        return None

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
            'tabs_json': self._tabs_json,
        }

    @properties.setter
    def properties(self, value):
        if not value:
            return
        self._binding_field = value.get('binding_field', '')
        self._entity_alias = value.get('entity_alias', '')
        self._is_required = value.get('is_required', False)
        self._is_readonly = value.get('is_readonly', False)
        if 'tabs_json' in value:
            self._tabs_json = value['tabs_json']
            self._load_tabs()

    def set_value(self, value):
        pass

    def get_value(self):
        return None

    def is_dirty(self):
        return False

    def reset(self):
        pass