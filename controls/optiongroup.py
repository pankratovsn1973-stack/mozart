# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/optiongroup.py

from PySide6.QtWidgets import QWidget, QButtonGroup, QVBoxLayout, QHBoxLayout, QRadioButton
from PySide6.QtCore import Property, Signal, Qt
import json
from .base_control import BaseControl
from .data_source_mixin import DataSourceMixin


class MozartOptionGroup(QWidget, BaseControl, DataSourceMixin):
    value_changed = Signal(str)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)
        DataSourceMixin.__init__(self)
        self._orientation = "vertical"
        self._button_group = QButtonGroup(self)
        self._radio_buttons = []
        self._button_group.buttonClicked.connect(self._on_button_clicked)
        # Создаём пустой layout сразу, чтобы избежать ошибки
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)

    def _on_button_clicked(self, button):
        self._is_dirty = button.property('value') != self._original_value
        self.value_changed.emit(button.property('value'))

    def _apply_readonly(self):
        for btn in self._radio_buttons:
            btn.setEnabled(not self._is_readonly)

    def _clear_layout(self):
        """Удаляет все виджеты из layout."""
        if self._main_layout:
            while self._main_layout.count():
                item = self._main_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def _update_control(self):
        """Обновляет радиокнопки из источника данных."""
        # Удаляем старые кнопки
        for btn in self._radio_buttons:
            self._button_group.removeButton(btn)
        self._radio_buttons.clear()
        self._clear_layout()

        # Создаём layout заново (если orientation изменился)
        if self._orientation == "horizontal":
            if not isinstance(self._main_layout, QHBoxLayout):
                self._clear_layout()
                self._main_layout = QHBoxLayout(self)
                self._main_layout.setContentsMargins(5, 5, 5, 5)
        else:
            if not isinstance(self._main_layout, QVBoxLayout):
                self._clear_layout()
                self._main_layout = QVBoxLayout(self)
                self._main_layout.setContentsMargins(5, 5, 5, 5)

        # Создаём кнопки из элементов
        for item in self.get_items():
            rb = QRadioButton(item["text"], self)
            rb.setProperty('value', item["value"])
            rb.setEnabled(not self._is_readonly)
            if self._design_mode:
                rb.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._button_group.addButton(rb)
            self._main_layout.addWidget(rb)
            self._radio_buttons.append(rb)

        self._main_layout.addStretch()

    @Property(str)
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        if value in ("vertical", "horizontal"):
            self._orientation = value
            if not self._design_mode:
                self._update_control()

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
            'source_type': self._source_type,
            'entity_alias': self._entity_alias,
            'display_field': self._display_field,
            'value_field': self._value_field,
            'items_json': self._items_json,
            'orientation': self._orientation,
            'filter_expression': self._filter_expression,
            'order_by': self._order_by,
            'query': self._query,
        })
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'source_type' in value:
            self._source_type = value['source_type']
        if 'entity_alias' in value:
            self._entity_alias = value['entity_alias']
        if 'display_field' in value:
            self._display_field = value['display_field']
        if 'value_field' in value:
            self._value_field = value['value_field']
        if 'items_json' in value:
            self._items_json = value['items_json']
        if 'orientation' in value:
            self._orientation = value['orientation']
        if 'filter_expression' in value:
            self._filter_expression = value['filter_expression']
        if 'order_by' in value:
            self._order_by = value['order_by']
        if 'query' in value:
            self._query = value['query']
        if not self._design_mode:
            self.load_items()

    def set_value(self, value):
        self.blockSignals(True)
        if isinstance(value, str) and not value.isdigit():
            value = self.find_value_by_text(value)
        for btn in self._radio_buttons:
            if btn.property('value') == value:
                btn.setChecked(True)
                break
        else:
            for btn in self._radio_buttons:
                btn.setChecked(False)
        self._original_value = value
        self._is_dirty = False
        self.blockSignals(False)

    def get_value(self):
        btn = self._button_group.checkedButton()
        return btn.property('value') if btn else None

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self.set_value(self._original_value)