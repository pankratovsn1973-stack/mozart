# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/combobox.py

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Property, Signal
import json
from .base_control import BaseControl
from .data_source_mixin import DataSourceMixin


class MozartComboBox(QComboBox, DataSourceMixin, BaseControl):
    # Объявляем сигналы на уровне QObject
    value_changed = Signal(object)
    items_loaded = Signal()

    def __init__(self, parent=None):
        # Вызываем конструктор базового QComboBox
        QComboBox.__init__(self, parent)
        # Вызываем миксины через правильную иерархию MRO
        DataSourceMixin.__init__(self)
        BaseControl.__init__(self)
        self._design_mode = False
        self.currentIndexChanged.connect(self._on_index_changed)

    def _on_index_changed(self, index):
        self._is_dirty = self.currentData() != self._original_value
        self.value_changed.emit(self.currentData())

    def _apply_readonly(self):
        self.setEnabled(not self._is_readonly)

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        self.setEnabled(not design_mode)

    def _update_control(self):
        self.clear()
        for item in self.get_items():
            self.addItem(item["text"], item["value"])

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
        index = self.findData(value)
        if index >= 0:
            self.setCurrentIndex(index)
        self._original_value = self.currentData()
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        return self.currentData()

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self.set_value(self._original_value)
