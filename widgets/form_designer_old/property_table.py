# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/property_table.py

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QHeaderView
from PySide6.QtCore import Qt, Signal


class PropertyTableWidget(QTableWidget):
    """Базовый UI-виджет инспектора свойств с изолированной логикой ячеек."""
    cell_value_committed = Signal(str, object)  # (prop_name, converted_value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Свойство", "Значение"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemChanged.connect(self._on_cell_changed)
        self.block_sync = False

    def add_property_row(self, label: str, prop_name: str, value, val_type: str = "str", readonly: bool = False):
        """Добавляет строго типизированную строку свойства в таблицу."""
        row = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(label)
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        name_item.setData(Qt.ItemDataRole.UserRole, prop_name)

        if val_type == "bool":
            str_value = "True" if value else "False"
        else:
            str_value = str(value) if value is not None else ""

        val_item = QTableWidgetItem(str_value)
        val_item.setData(Qt.ItemDataRole.UserRole, val_type)

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if not readonly:
            flags |= Qt.ItemFlag.ItemIsEditable
        val_item.setFlags(flags)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, val_item)

    def _on_cell_changed(self, item):
        """Обрабатывает ручной ввод пользователя в ячейку значения (Колонка 1)."""
        if self.block_sync or item.column() != 1:
            return

        row = item.row()
        name_item = self.item(row, 0)
        if not name_item:
            return

        prop_name = name_item.data(Qt.ItemDataRole.UserRole)
        raw_value = item.text().strip()
        orig_type = item.data(Qt.ItemDataRole.UserRole)

        # Безопасный перехват пустых строк для числовых полей
        if raw_value == "" and orig_type in ("int", "float"):
            self.cell_value_committed.emit(prop_name, 0)
            return

        try:
            if orig_type == "bool":
                new_value = raw_value.lower() in ("true", "1", "да", "yes")
            elif orig_type in ("int", "float"):
                new_value = int(float(raw_value)) if orig_type == "int" else float(raw_value)
            else:
                new_value = raw_value
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", f"Некорректный формат свойства '{prop_name}'!")
            return

        self.cell_value_committed.emit(prop_name, new_value)
