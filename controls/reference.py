# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/reference.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QLabel
from PySide6.QtCore import Property, Signal, Qt

from .base_control import BaseControl


class MozartReference(QWidget, BaseControl):
    value_changed = Signal(object)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)

        # Настройки ERP метаданных
        self._binding_field = ""
        self._entity_alias = ""
        self._display_field = "cname"
        self._selector_form = ""

        self._current_id = None
        self._display_value = ""
        self._db = None
        self._label = "Ссылка:"
        self._design_mode = False
        self.layout_assigned = None

        self.edit_runtime = None  # Для рантайма (QLineEdit)
        self.edit_design = None  # Для дизайнера (QLabel-заглушка)

        self.init_ui()

        if hasattr(self, '_properties') and self._properties:
            self.properties = self._properties

    def init_ui(self):
        # Дефолтная сборка для рантайма
        self.layout_assigned = QHBoxLayout(self)
        self.layout_assigned.setContentsMargins(0, 0, 0, 0)
        self.layout_assigned.setSpacing(6)

        # --- МЕТКА (LABEL) ---
        self.label_widget = QLabel(self)
        self.label_widget.setObjectName("lbl_of_ref")
        self.label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.layout_assigned.addWidget(self.label_widget)

        # --- ПОЛЕ РАНТАЙМА ---
        self.edit_runtime = QLineEdit(self)
        self.edit_runtime.setObjectName("txt_of_ref")
        self.edit_runtime.setReadOnly(True)
        self.layout_assigned.addWidget(self.edit_runtime)

        # --- КНОПКА ВЫБОРА ---
        self.btn_select = QPushButton("📁", self)
        self.btn_select.setObjectName("btn_select_of_ref")
        self.btn_select.setFixedWidth(28)
        self.layout_assigned.addWidget(self.btn_select)

        # --- КНОПКА ОЧИСТКИ ---
        self.btn_clear = QPushButton("✖", self)
        self.btn_clear.setObjectName("btn_clear_of_ref")
        self.btn_clear.setFixedWidth(28)
        self.layout_assigned.addWidget(self.btn_clear)

        self._update_label()

    def _update_label(self):
        if hasattr(self, 'label_widget') and self.label_widget:
            if self._label and self._label.strip():
                self.label_widget.setText(self._label)
                self.label_widget.setVisible(True)
                if not self._design_mode:
                    self.label_widget.setMinimumWidth(
                        self.label_widget.fontMetrics().horizontalAdvance(self._label) + 5)
            else:
                self.label_widget.setText("")
                self.label_widget.setVisible(False)

    def set_design_mode(self, design_mode):
        """Динамическое переключение макета под режим дизайна или рантайма."""
        self._design_mode = design_mode
        self.btn_select.setEnabled(not design_mode)
        self.btn_clear.setEnabled(not design_mode)

        if design_mode and self.layout_assigned:
            # Запоминаем геометрию элементов
            geo_label = self.label_widget.geometry()
            geo_runtime_edit = self.edit_runtime.geometry()
            geo_select = self.btn_select.geometry()
            geo_clear = self.btn_clear.geometry()

            # Удаляем живой QLineEdit рантайма
            self.edit_runtime.deleteLater()
            self.edit_runtime = None

            # Подменяем безопасной QLabel-заглушкой с внешним видом текстбокса
            self.edit_design = QLabel(self)
            self.edit_design.setObjectName("txt_of_ref")
            self.edit_design.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.edit_design.setStyleSheet(
                "border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px; color: #555555;"
            )
            self.edit_design.setText(f"Справочник: {self._entity_alias}" if self._entity_alias else "Не выбрано")
            self.edit_design.show()

            # Сносим макет для перехода на абсолютные координаты
            while self.layout_assigned.count() > 0:
                item = self.layout_assigned.takeAt(0)
                if item.widget():
                    item.widget().setParent(self)

            self.layout_assigned.deleteLater()
            self.layout_assigned = None

            # Сажаем элементы на их физические координаты
            self.label_widget.setGeometry(geo_label)
            self.edit_design.setGeometry(geo_runtime_edit)
            self.btn_select.setGeometry(geo_select)
            self.btn_clear.setGeometry(geo_clear)

    @Property(str)
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = str(value)
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
        if self._design_mode and self.edit_design:
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

    @is_required.setter
    def is_required(self, value):
        self._is_required = bool(value)
        target = self.edit_design if self._design_mode else self.edit_runtime
        if target:
            if self._is_required:
                target.setStyleSheet("border: 1px solid #ff4d4d; background-color: #fff2f2; padding-left: 5px;")
            else:
                if self._design_mode:
                    target.setStyleSheet(
                        "border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px; color: #555555;")
                else:
                    target.setStyleSheet("")

    @Property(bool)
    def is_readonly(self):
        return getattr(self, '_is_readonly', False)

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = bool(value)

    def set_db(self, db):
        self._db = db

    def set_value(self, instance_id, display_value=None):
        self._current_id = instance_id
        if display_value is not None:
            self._display_value = display_value
        else:
            self._display_value = f"Справочник: {self._entity_alias}" if self._entity_alias else "Не выбрано"

        if self.edit_runtime:
            self.edit_runtime.setText(self._display_value)
        elif self.edit_design:
            self.edit_design.setText(self._display_value)

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
        if not value: return
        self._binding_field = value.get('binding_field', '')
        self._entity_alias = value.get('entity_alias', '')
        self._display_field = value.get('display_field', 'cname')
        self._selector_form = value.get('selector_form', '')
        self.is_required = value.get('is_required', False)
        self.is_readonly = value.get('is_readonly', False)
        if 'label' in value:
            self._label = value['label']
            self._update_label()
