# mozart_import/designer/designer_mass_field_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QSpinBox, QDialogButtonBox
from PySide6.QtCore import Qt

from .designer_utils import to_field_name


class MassFieldDialog(QDialog):
    def __init__(self, parent, source_fields, translator):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.tr('mass_field_dialog_title'))
        self.resize(800, 500)
        layout = QVBoxLayout(self)

        self.table = QTableWidget(len(source_fields), 4)
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('source_field'),
            self.translator.tr('mozart_field_name'),
            self.translator.tr('type'),
            self.translator.tr('length')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)

        for row, sf in enumerate(source_fields):
            self.table.setItem(row, 0, QTableWidgetItem(sf['source_field_name']))
            suggested = to_field_name(sf['source_field_name'])
            name_item = QTableWidgetItem(suggested)
            self.table.setItem(row, 1, name_item)
            type_combo = QComboBox()
            type_combo.addItems(["C", "N", "I", "D", "T", "L", "M", "R"])
            type_combo.setCurrentText("C")
            self.table.setCellWidget(row, 2, type_combo)
            length_spin = QSpinBox()
            length_spin.setRange(1, 10000)
            length_spin.setValue(255)
            self.table.setCellWidget(row, 3, length_spin)

        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_fields(self):
        fields = []
        for row in range(self.table.rowCount()):
            source_field = self.table.item(row, 0).text()
            target_field = self.table.item(row, 1).text()
            type_combo = self.table.cellWidget(row, 2)
            length_spin = self.table.cellWidget(row, 3)
            if target_field:
                fields.append({
                    'source_field': source_field,
                    'cfieldname': target_field,
                    'cfieldtype': type_combo.currentText(),
                    'nlength': length_spin.value(),
                    'calias': source_field.capitalize()[:50]
                })
        return fields