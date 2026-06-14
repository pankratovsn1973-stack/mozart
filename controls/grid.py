# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/grid.py

import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QHBoxLayout, QLabel
from PySide6.QtCore import Property, Qt

from .base_control import BaseControl


class MozartGrid(QWidget, BaseControl):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)
        self._columns_json = "[]"
        self._allow_filter = True
        self._allow_sort = True
        self._label = ""
        self._data = []
        self._filtered_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Введите текст для фильтрации...")
        self.filter_edit.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_edit)
        layout.addLayout(filter_layout)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        self.filter_edit.setVisible(self._allow_filter)

    def set_design_mode(self, design_mode):
        self.filter_edit.setEnabled(not design_mode)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

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
        self.table.setEditTriggers(QTableWidget.NoEditTriggers if value else QTableWidget.DoubleClicked)

    @Property(str)
    def columns_json(self):
        return self._columns_json

    @columns_json.setter
    def columns_json(self, value):
        self._columns_json = value
        self._setup_columns()

    @Property(bool)
    def allow_filter(self):
        return self._allow_filter

    @allow_filter.setter
    def allow_filter(self, value):
        self._allow_filter = value
        self.filter_edit.setVisible(value)

    @Property(bool)
    def allow_sort(self):
        return self._allow_sort

    @allow_sort.setter
    def allow_sort(self, value):
        self._allow_sort = value
        self.table.setSortingEnabled(value)

    def _setup_columns(self):
        try:
            columns = json.loads(self._columns_json)
            self.table.setColumnCount(len(columns))
            for i, col in enumerate(columns):
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(col.get('header', col.get('field', ''))))
                if col.get('width'):
                    self.table.setColumnWidth(i, col['width'])
        except:
            pass

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
            'columns_json': self._columns_json,
            'allow_filter': self._allow_filter,
            'allow_sort': self._allow_sort,
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
        if 'columns_json' in value:
            self._columns_json = value['columns_json']
            self._setup_columns()
        if 'allow_filter' in value:
            self._allow_filter = value['allow_filter']
            self.filter_edit.setVisible(self._allow_filter)
        if 'allow_sort' in value:
            self._allow_sort = value['allow_sort']
            self.table.setSortingEnabled(self._allow_sort)

    def set_data(self, data):
        self._data = data
        self._filtered_data = data[:]
        self.refresh()

    def refresh(self):
        self.table.setRowCount(len(self._filtered_data))
        try:
            columns = json.loads(self._columns_json)
        except:
            columns = []
        for row, item in enumerate(self._filtered_data):
            for col_idx, col in enumerate(columns):
                field = col.get('field')
                value = item.get(field, '') if isinstance(item, dict) else getattr(item, field, '') if hasattr(item, field) else ''
                self.table.setItem(row, col_idx, QTableWidgetItem(str(value)))

    def on_filter_changed(self, text):
        if not text:
            self._filtered_data = self._data[:]
        else:
            text_lower = text.lower()
            self._filtered_data = []
            try:
                columns = json.loads(self._columns_json)
            except:
                columns = []
            for item in self._data:
                match = False
                for col in columns:
                    field = col.get('field')
                    value = item.get(field, '') if isinstance(item, dict) else getattr(item, field, '') if hasattr(item, field) else ''
                    if text_lower in str(value).lower():
                        match = True
                        break
                if match:
                    self._filtered_data.append(item)
        self.refresh()

    def get_selected(self):
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self._filtered_data):
            return self._filtered_data[current_row]
        return None

    def set_value(self, value):
        pass

    def get_value(self):
        return self.get_selected()

    def is_dirty(self):
        return False

    def reset(self):
        pass