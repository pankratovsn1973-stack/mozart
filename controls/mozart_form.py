# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/mozart_form.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Property, Signal, Qt


class MozartForm(QWidget):
    form_loaded = Signal()
    form_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entity_alias = ""
        self._instance_id = 0
        self._caller_form = ""
        self._form_index = 0
        self._open_params = ""
        self._is_modal = False
        self._is_readonly = False
        self._data_bridge = None
        self._design_mode = False

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        for child in self.findChildren(QWidget):
            if hasattr(child, 'set_design_mode'):
                child.set_design_mode(design_mode)

    @Property(str)
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value

    @Property(int)
    def instance_id(self):
        return self._instance_id if self._instance_id is not None else 0

    @instance_id.setter
    def instance_id(self, value):
        self._instance_id = value if value != 0 else 0

    @Property(str)
    def caller_form(self):
        return self._caller_form

    @caller_form.setter
    def caller_form(self, value):
        self._caller_form = value

    @Property(int)
    def form_index(self):
        return self._form_index

    @form_index.setter
    def form_index(self, value):
        self._form_index = value

    @Property(str)
    def open_params(self):
        return self._open_params

    @open_params.setter
    def open_params(self, value):
        self._open_params = value

    @Property(bool)
    def is_modal(self):
        return self._is_modal

    @is_modal.setter
    def is_modal(self, value):
        self._is_modal = value
        if value:
            self.setWindowModality(Qt.ApplicationModal)
        else:
            self.setWindowModality(Qt.NonModal)

    @Property(bool)
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        self._apply_readonly()

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        return {
            'entity_alias': self._entity_alias,
            'instance_id': self._instance_id,
            'caller_form': self._caller_form,
            'form_index': self._form_index,
            'open_params': self._open_params,
            'is_modal': self._is_modal,
            'is_readonly': self._is_readonly,
        }

    @properties.setter
    def properties(self, value):
        if not value:
            return
        self._entity_alias = value.get('entity_alias', '')
        self._instance_id = value.get('instance_id', 0)
        self._caller_form = value.get('caller_form', '')
        self._form_index = value.get('form_index', 0)
        self._open_params = value.get('open_params', '')
        self._is_modal = value.get('is_modal', False)
        self._is_readonly = value.get('is_readonly', False)

    def set_data_bridge(self, bridge):
        self._data_bridge = bridge

    def load_data(self):
        if not self._data_bridge or not self._entity_alias or not self._instance_id:
            return
        data = self._data_bridge.get_item(self._entity_alias, self._instance_id)
        if data:
            self._populate_controls(data)
            self.form_loaded.emit()

    def save(self):
        if not self._data_bridge or not self._entity_alias:
            return
        data = self._collect_data()
        result = self._data_bridge.save_item(self._entity_alias, self._instance_id, data)
        if result and result.get('success'):
            self._instance_id = result.get('instance_id')
            self.form_saved.emit()
        return result

    def _populate_controls(self, data):
        pass

    def _collect_data(self):
        return {}

    def _apply_readonly(self):
        for child in self.findChildren(QWidget):
            if hasattr(child, 'setReadOnly'):
                child.setReadOnly(self._is_readonly)
            elif hasattr(child, 'setEnabled'):
                child.setEnabled(not self._is_readonly)