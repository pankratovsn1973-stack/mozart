# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/form.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal

from .base_control import BaseControl
from .container import MozartContainer
from .tab_container import MozartTabContainer


class Form(QWidget):
    form_modified = Signal(bool)
    form_saved = Signal()
    form_closed = Signal()

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self._form_id = None
        self._form_alias = ""
        self._entity_alias = ""
        self._instance_id = None
        self._is_new = True
        self._readonly = False
        self._controls = {}
        self._title = ""
        self._design_mode = False
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout = QHBoxLayout()
        self.main_layout.addLayout(self.toolbar_layout)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        for control in self._controls.values():
            if hasattr(control, 'set_design_mode'):
                control.set_design_mode(design_mode)

    @property
    def form_id(self):
        return self._form_id

    @form_id.setter
    def form_id(self, value):
        self._form_id = value

    @property
    def form_alias(self):
        return self._form_alias

    @form_alias.setter
    def form_alias(self, value):
        self._form_alias = value

    @property
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value

    @property
    def instance_id(self):
        return self._instance_id

    @instance_id.setter
    def instance_id(self, value):
        self._instance_id = value
        self._is_new = (value is None)

    @property
    def is_new(self):
        return self._is_new

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, value):
        self._readonly = value
        for control in self._controls.values():
            if hasattr(control, 'setReadOnly'):
                control.setReadOnly(value)
            elif hasattr(control, 'setEnabled'):
                control.setEnabled(not value)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.setWindowTitle(value)

    @property
    def is_modified(self):
        for control in self._controls.values():
            if hasattr(control, 'is_dirty'):
                if callable(control.is_dirty) and control.is_dirty():
                    return True
                elif isinstance(control.is_dirty, bool) and control.is_dirty:
                    return True
        return False

    def add_control(self, alis, control):
        self._controls[alis] = control
        self.content_layout.addWidget(control)
        if hasattr(control, 'textChanged'):
            control.textChanged.connect(self.on_control_changed)
        elif hasattr(control, 'stateChanged'):
            control.stateChanged.connect(self.on_control_changed)
        elif hasattr(control, 'currentIndexChanged'):
            control.currentIndexChanged.connect(self.on_control_changed)
        elif hasattr(control, 'value_changed'):
            control.value_changed.connect(self.on_control_changed)

    def get_control(self, alis):
        return self._controls.get(alis)

    def remove_control(self, alis):
        if alis in self._controls:
            control = self._controls[alis]
            self.content_layout.removeWidget(control)
            control.deleteLater()
            del self._controls[alis]

    def clear_controls(self):
        for alis, control in list(self._controls.items()):
            self.content_layout.removeWidget(control)
            control.deleteLater()
        self._controls.clear()

    def load_data(self, data):
        for alis, control in self._controls.items():
            if alis in data:
                control.blockSignals(True)
                if hasattr(control, 'set_value'):
                    control.set_value(data[alis])
                elif hasattr(control, 'value'):
                    control.value = data[alis]
                control.blockSignals(False)
        self.form_modified.emit(False)

    def get_data(self):
        result = {}
        for alis, control in self._controls.items():
            if hasattr(control, 'get_value'):
                result[alis] = control.get_value()
            elif hasattr(control, 'value'):
                result[alis] = control.value
        return result

    def save(self):
        pass

    def rollback(self):
        for control in self._controls.values():
            if hasattr(control, 'reset'):
                control.reset()
            elif hasattr(control, 'rollback'):
                control.rollback()
        self.form_modified.emit(False)

    def on_control_changed(self):
        self.form_modified.emit(self.is_modified)

    def on_open(self, **params):
        pass

    def on_close(self):
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Есть несохранённые изменения. Сохранить?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                self.save()
        return True

    def closeEvent(self, event):
        if self.on_close():
            self.form_closed.emit()
            event.accept()
        else:
            event.ignore()