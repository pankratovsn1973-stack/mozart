# widgets/form_designer_old/property_editor.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс PropertyEditor (Инспектор свойств).
Отвечает за отображение и редактирование параметров активных контролов холста.
Исправлен баг отсутствия метода set_active_item (исправление AttributeError).
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox
from PySide6.QtCore import Qt, Signal, QPointF


class PropertyEditor(QTableWidget):
    """
    Табличный инспектор свойств в стиле FoxPro Property Sheet.
    Обеспечивает двухстороннюю связь между таблицей и графическим холстом.
    """
    property_changed = Signal(str, str, object)  # (control_id, prop_name, new_value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Свойство", "Значение"])
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)

        self.current_item = None
        self.current_control_id = None

        self._block_sync = False
        self.itemChanged.connect(self._on_cell_edited)

    def set_active_item(self, control_id: str, item_obj):
        """
        ИСПРАВЛЕНО: Главный метод загрузки параметров активного элемента.
        Вызывается из main_widget.py при старте формы и смене фокуса.
        """
        self.current_item = item_obj
        self.current_control_id = control_id

        self._block_sync = True
        self.clearContents()
        self.setRowCount(0)

        if not self.current_item:
            self._block_sync = False
            return

        # Если у объекта есть title_bar — значит это сама форма (FormBackground)
        if hasattr(self.current_item, 'title_bar'):
            self._load_form_properties()
        else:
            self._load_control_properties()

        self._block_sync = False

    def _load_form_properties(self):
        """Заполнение таблицы свойствами проектируемой формы."""
        bg = self.current_item
        properties = [
            ("Имя формы (Alias)", "form_alias", getattr(bg, 'form_alias', '')),
            ("Заголовок окна", "title", getattr(bg, 'title', '')),
            ("Ширина формы", "width", int(bg.width)),
            ("Высота формы", "height", int(bg.height)),
        ]
        for label, prop_name, value in properties:
            self._add_property_row(label, prop_name, value)

    def _load_control_properties(self):
        """Заполнение таблицы свойствами выбранного элемента управления."""
        proxy = self.current_item
        rect = proxy.rect()
        pos = proxy.pos()

        properties = [
            ("ID Контрола", "control_id", getattr(proxy, 'control_id', '')),
            ("Тип поля", "control_type", getattr(proxy, 'control_type', '')),
            ("Координата X (Left)", "x", int(pos.x())),
            ("Координата Y (Top)", "y", int(pos.y())),
            ("Ширина (Width)", "width", int(rect.width())),
            ("Высота (Height)", "height", int(rect.height())),
        ]

        inner_widget = proxy.widget()
        if inner_widget:
            if hasattr(inner_widget, 'text') and callable(inner_widget.text):
                properties.append(("Отображаемый текст", "text", inner_widget.text()))
            if hasattr(inner_widget, 'source_name'):
                properties.append(("Поле БД (Source)", "source_name", getattr(inner_widget, 'source_name', '')))

        for label, prop_name, value in properties:
            self._add_property_row(label, prop_name, value)

    def _add_property_row(self, label: str, prop_name: str, value):
        """Добавление строки параметров в таблицу."""
        row = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(label)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        name_item.setData(Qt.UserRole, prop_name)

        val_item = QTableWidgetItem(str(value))
        val_item.setData(Qt.UserRole, type(value))

        if prop_name in ["control_id", "control_type"]:
            val_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, val_item)

    def _on_cell_edited(self, item):
        """Обработчик изменения значения ячейки инспектора пользователем."""
        if self._block_sync or item.column() != 1 or not self.current_item:
            return

        row = item.row()
        name_item = self.item(row, 0)
        if not name_item:
            return

        prop_name = name_item.data(Qt.UserRole)
        raw_value = item.text().strip()
        orig_type = item.data(Qt.UserRole)

        try:
            new_value = int(raw_value) if orig_type == int else str(raw_value)
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Некорректный формат числового значения!")
            return

        self._apply_property_to_item(prop_name, new_value)
        self.property_changed.emit(self.current_control_id, prop_name, new_value)

    def _apply_property_to_item(self, prop_name: str, value):
        """Прямая аппаратная модификация параметров геометрии объекта на визуальной сцене."""
        obj = self.current_item

        if hasattr(obj, 'title_bar'):
            if prop_name == "title":
                obj.title = str(value)
                if obj.scene(): obj.scene().update()
            elif prop_name == "width":
                obj.set_width(float(value))
            elif prop_name == "height":
                obj.set_height(float(value))
        else:
            pos = obj.pos()
            if prop_name == "x":
                obj.setPos(float(value), pos.y())
            elif prop_name == "y":
                obj.setPos(pos.x(), float(value))
            elif prop_name == "width":
                obj.setWidgetSize(float(value), obj.rect().height())
            elif prop_name == "height":
                obj.setWidgetSize(obj.rect().width(), float(value))
            elif prop_name == "text":
                inner_w = obj.widget()
                if inner_w and hasattr(inner_w, 'setText'):
                    inner_w.setText(str(value))
