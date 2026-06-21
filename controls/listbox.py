# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/listbox.py

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Property, Qt, Signal
import json
from .base_control import BaseControl
from .data_source_mixin import DataSourceMixin


class MozartListBox(QListWidget, DataSourceMixin, BaseControl):
    value_changed = Signal(object)
    items_loaded = Signal()

    def __init__(self, parent=None):
        QListWidget.__init__(self, parent)
        DataSourceMixin.__init__(self)
        BaseControl.__init__(self)
        self._design_mode = False
        self._original_value = None
        self._is_dirty = False
        self.currentItemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, current, previous):
        if current:
            val = current.data(Qt.ItemDataRole.UserRole)
            self._is_dirty = val != self._original_value
            self.value_changed.emit(val)
        else:
            self._is_dirty = self._original_value is not None
            self.value_changed.emit(None)

    def _apply_readonly(self):
        self.setEnabled(not self._is_readonly)

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        self.setEnabled(not design_mode)

    def _update_control(self):
        self.clear()
        for item in self.get_items():
            list_item = QListWidgetItem(item["text"])
            list_item.setData(Qt.ItemDataRole.UserRole, item["value"])
            self.addItem(list_item)

    @Property(str)
    def binding_field(self):
        return self._binding_field

    @Property(str)
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
            self.setStyleSheet(self.styleSheet() + " border: 1px solid red;")
        else:
            self.setStyleSheet(self.styleSheet().replace(" border: 1px solid red;", ""))

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
        props.update({
            'source_type': getattr(self, '_source_type', 'static'),
            'entity_alias': self._entity_alias,
            'display_field': getattr(self, '_display_field', 'cname'),
            'value_field': getattr(self, '_value_field', 'id'),
            'items_json': getattr(self, '_items_json', '[]'),
            'filter_expression': getattr(self, '_filter_expression', ''),
            'order_by': getattr(self, '_order_by', ''),
            'query': getattr(self, '_query', ''),
        })
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'source_type' in value: self._source_type = value['source_type']
        if 'entity_alias' in value: self._entity_alias = value['entity_alias']
        if 'display_field' in value: self._display_field = value['display_field']
        if 'value_field' in value: self._value_field = value['value_field']
        if 'items_json' in value: self._items_json = value['items_json']
        if 'filter_expression' in value: self._filter_expression = value['filter_expression']
        if 'order_by' in value: self._order_by = value['order_by']
        if 'query' in value: self._query = value['query']

        if not getattr(self, '_design_mode', False):
            self.load_items()

    def set_value(self, value):
        self.blockSignals(True)
        if isinstance(value, str) and not value.isdigit():
            if hasattr(self, 'find_value_by_text'):
                value = self.find_value_by_text(value)
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == value:
                self.setCurrentItem(item)
                break
        else:
            self.setCurrentItem(None)
        self._original_value = value
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        item = self.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self.set_value(self._original_value)
