# widgets/form_designer_old/property_panel.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QSpinBox, QLabel
from PySide6.QtCore import Qt


class PropertyPanel(QWidget):
    """Панель свойств контрола"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_control = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.info_label = QLabel("Контрол не выбран")
        self.info_label.setStyleSheet("color: gray;")
        layout.addWidget(self.info_label)

        form = QFormLayout()

        self.edit_alias = QLineEdit()
        form.addRow("Алиас:", self.edit_alias)

        self.edit_binding = QLineEdit()
        form.addRow("Привязка:", self.edit_binding)

        self.chk_required = QCheckBox()
        form.addRow("Обязательное:", self.chk_required)

        self.chk_readonly = QCheckBox()
        form.addRow("Только чтение:", self.chk_readonly)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(20, 2000)
        form.addRow("Ширина:", self.spin_width)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(20, 1000)
        form.addRow("Высота:", self.spin_height)

        layout.addLayout(form)
        layout.addStretch()

    def set_control(self, control_item):
        self.current_control = control_item
        if control_item:
            data = control_item.get_data()
            self.info_label.setText(f"{data['type']}: {data['alias']}")
            self.edit_alias.setText(data['alias'])
            self.spin_width.setValue(data['width'])
            self.spin_height.setValue(data['height'])
            self.setEnabled(True)
        else:
            self.info_label.setText("Контрол не выбран")
            self.setEnabled(False)

    def get_properties(self):
        return {
            'alias': self.edit_alias.text(),
            'binding_field': self.edit_binding.text(),
            'is_required': self.chk_required.isChecked(),
            'is_readonly': self.chk_readonly.isChecked(),
            'width': self.spin_width.value(),
            'height': self.spin_height.value()
        }