# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/reference_ui.py

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from .reference_base import MozartReferenceBase


class MozartReference(MozartReferenceBase):
    """Визуальное представление ERP-компонента Ссылка с логикой переключения режимов."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_assigned = None
        self.edit_runtime = None
        self.edit_design = None
        self.init_ui()

        if hasattr(self, '_properties') and self._properties:
            self.properties = self._properties

    def init_ui(self):
        # Стартовый дефолтный размер самого референса целиком при Init (как рубль)
        self.setFixedSize(250, 30)

        self.layout_assigned = QHBoxLayout(self)
        self.layout_assigned.setContentsMargins(0, 0, 0, 0)
        self.layout_assigned.setSpacing(6)
        self.layout_assigned.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.label_widget = QLabel(self)
        self.label_widget.setObjectName("lbl_of_ref")
        self.label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_widget.setFixedSize(60, 26)  # Стартовые цифры надписи
        self.layout_assigned.addWidget(self.label_widget)

        self.edit_runtime = QLineEdit(self)
        self.edit_runtime.setObjectName("txt_of_ref")
        self.edit_runtime.setReadOnly(True)
        self.edit_runtime.setFixedHeight(26)  # Стартовая высота текстового поля
        self.layout_assigned.addWidget(self.edit_runtime)

        self.btn_select = QPushButton("📁", self)
        self.btn_select.setObjectName("btn_select_of_ref")
        self.btn_select.setFixedSize(28, 26)  # Стартовые цифры кнопки выбора
        self.layout_assigned.addWidget(self.btn_select)

        self.btn_clear = QPushButton("✖", self)
        self.btn_clear.setObjectName("btn_clear_of_ref")
        self.btn_clear.setFixedSize(28, 26)  # Стартовые цифры кнопки очистки
        self.layout_assigned.addWidget(self.btn_clear)

        self._update_label()

    def _update_label(self):
        if hasattr(self, 'label_widget') and self.label_widget:
            if self._label and self._label.strip():
                self.label_widget.setText(self._label)
                self.label_widget.setVisible(True)
                if not self._design_mode:
                    self.label_widget.setMinimumWidth(
                        self.label_widget.fontMetrics().horizontalAdvance(self._label) + 5
                    )
            else:
                self.label_widget.setText("")
                self.label_widget.setVisible(False)

    def set_design_mode(self, design_mode):
        """Бесшумная подмена инпута внутри макета на чистых фиксированных цифрах."""
        self._design_mode = design_mode
        self.btn_select.setEnabled(not design_mode)
        self.btn_clear.setEnabled(not design_mode)

        if design_mode and self.layout_assigned:
            # Находим позицию оригинального QLineEdit в макете
            idx = self.layout_assigned.indexOf(self.edit_runtime)
            if idx >= 0:
                # Извлекаем и удаляем рантайм-инпут
                item = self.layout_assigned.takeAt(idx)
                if item.widget():
                    item.widget().deleteLater()
                self.edit_runtime = None

                # Строим легкую дизайн-заглушку
                self.edit_design = QLabel(self)
                self.edit_design.setObjectName("txt_of_ref")
                self.edit_design.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.edit_design.setStyleSheet(
                    "border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px; color: #555555;"
                )
                self.edit_design.setText(f"Справочник: {self._entity_alias}" if self._entity_alias else "Не выбрано")

                # ЖЕСТКАЯ ФИКСАЦИЯ: Прописываем заглушке чистые дефолтные цифры при ините
                self.edit_design.setFixedSize(120, 26)

                # Возвращаем заглушку в макет на то же место
                self.layout_assigned.insertWidget(idx, self.edit_design)
                self.edit_design.show()

            # Фиксируем габариты остальных потрохов, исключая любые прыжки геометрии
            if hasattr(self, 'label_widget') and self.label_widget:
                self.label_widget.setFixedSize(60, 26)
            self.btn_select.setFixedSize(28, 26)
            self.btn_clear.setFixedSize(28, 26)

    def set_required_state(self, value):
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

    def set_readonly_state(self, value):
        self._is_readonly = bool(value)

    def set_value(self, instance_id, display_value=None):
        self._current_id = instance_id
        self._display_value = display_value or (
            f"Справочник: {self._entity_alias}" if self._entity_alias else "Не выбрано")
        target = self.edit_runtime or self.edit_design
        if target:
            target.setText(self._display_value)
