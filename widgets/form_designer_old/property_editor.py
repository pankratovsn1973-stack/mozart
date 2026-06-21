# widgets/form_designer_old/property_editor.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QHeaderView
from PySide6.QtCore import Qt, Signal, QPointF


class PropertyEditor(QTableWidget):
    property_changed = Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Свойство", "Значение"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.current_item = None
        self.current_control_id = None
        self._block_sync = False
        self.itemChanged.connect(self._on_cell_edited)

    def set_control(self, control_item):
        """Интеграционный алиас для фокуса контрола со сцены."""
        if isinstance(control_item, list):
            control_item = control_item if len(control_item) > 0 else None

        if not control_item or control_item == getattr(self.parent(), 'runtime_form', None):
            self.set_form(self.parent())
            return

        c_id = getattr(control_item, 'control_id', 'unknown')
        self.set_active_item(c_id, control_item)

    def set_form(self, parent_designer):
        """Интеграционный алиас для фокуса на бланк формы."""
        form_obj = getattr(parent_designer, 'runtime_form', None)
        if form_obj:
            self.set_active_item("form_root", form_obj)
        else:
            self.set_active_item(None, None)

    def set_active_item(self, control_id: str, item_obj):
        """Устанавливает текущий объект для редактирования свойств."""
        self.current_item = item_obj
        self.current_control_id = control_id

        self._block_sync = True
        self.clearContents()
        self.setRowCount(0)

        if not self.current_item:
            self._block_sync = False
            return

        if hasattr(self.current_item, 'title_bar') or hasattr(self.current_item, 'resize_form'):
            self._load_form_properties()
        else:
            self._load_control_properties()

        self._block_sync = False

    def update_geometry_values(self, x, y, width, height):
        """ЭКСТРЕННЫЙ ОНЛАЙН-АПДЕЙТ: Точечно меняет координаты в таблице при драге мышью."""
        if self._block_sync or not self.current_item:
            return

        self._block_sync = True

        geo_map = {
            "x": str(int(x)),
            "y": str(int(y)),
            "width": str(int(width)),
            "height": str(int(height))
        }

        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            if name_item:
                prop_name = name_item.data(Qt.ItemDataRole.UserRole)
                if prop_name in geo_map:
                    val_item = self.item(row, 1)
                    if val_item:
                        val_item.setText(geo_map[prop_name])

        self._block_sync = False

    def _load_form_properties(self):
        """Загружает свойства формы."""
        bg = self.current_item
        pos = bg.pos()
        properties = [
            ("Имя формы (Alias)", "form_alias", getattr(bg, 'form_alias', 'Новая форма')),
            ("Заголовок окна", "title", getattr(bg, 'title', 'Форма')),
            ("Координата X (Left)", "x", int(pos.x())),
            ("Координата Y (Top)", "y", int(pos.y())),
            ("Ширина формы", "width", int(bg.width)),
            ("Высота формы", "height", int(bg.height)),
        ]
        for label, prop_name, value in properties:
            self._add_property_row(label, prop_name, value)

    def _load_control_properties(self):
        """Загружает свойства контрола."""
        proxy = self.current_item
        if not proxy:
            return

        try:
            rect = proxy.rect()
            pos = proxy.pos()
            width = int(rect.width()) if rect.width() else 150
            height = int(rect.height()) if rect.height() else 30
            x = int(pos.x()) if pos.x() else 0
            y = int(pos.y()) if pos.y() else 0
        except:
            width, height, x, y = 150, 30, 0, 0

        properties = [
            ("ID Контрола", "control_id", getattr(proxy, 'control_id', '')),
            ("Тип поля", "control_type", getattr(proxy, 'control_type', 'textbox')),
            ("Координата X (Left)", "x", x),
            ("Координата Y (Top)", "y", y),
            ("Ширина (Width)", "width", width),
            ("Высота (Height)", "height", height),
        ]

        inner_widget = proxy.widget()
        if inner_widget:
            if hasattr(inner_widget, 'text') and callable(inner_widget.text):
                try:
                    properties.append(("Отображаемый текст", "text", inner_widget.text() or ""))
                except:
                    pass
            if hasattr(inner_widget, 'objectName'):
                properties.append(("Имя объекта", "objectName", inner_widget.objectName() or ""))

        for label, prop_name, value in properties:
            self._add_property_row(label, prop_name, value)

    def _add_property_row(self, label: str, prop_name: str, value):
        """Добавляет строку в таблицу свойств."""
        row = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(label)
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        name_item.setData(Qt.ItemDataRole.UserRole, prop_name)

        try:
            str_value = str(value) if value is not None else ""
        except:
            str_value = ""

        val_item = QTableWidgetItem(str_value)
        val_item.setData(Qt.ItemDataRole.UserRole, type(value).__name__ if value is not None else "str")

        if prop_name in ["control_id", "control_type", "ID Контрола", "Тип поля"]:
            val_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, val_item)

    def _on_cell_edited(self, item):
        """Обработчик изменения значения свойства."""
        if self._block_sync or item.column() != 1 or not self.current_item:
            return

        row = item.row()
        name_item = self.item(row, 0)
        if not name_item:
            return

        prop_name = name_item.data(Qt.ItemDataRole.UserRole)
        raw_value = item.text().strip()
        orig_type = item.data(Qt.ItemDataRole.UserRole)

        try:
            if orig_type == "int" or orig_type == "float":
                if raw_value == "":
                    new_value = 0
                elif orig_type == "int":
                    new_value = int(float(raw_value))
                else:
                    new_value = float(raw_value)
            else:
                new_value = raw_value
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", f"Некорректный формат для {prop_name}!")
            old_item = self.item(row, 1)
            if old_item:
                item.setText(old_item.text())
            return

        self._apply_property_to_item(prop_name, new_value)
        self.property_changed.emit(self.current_control_id, prop_name, new_value)

    def _apply_property_to_item(self, prop_name: str, value):
        """Применяет изменение свойства к объекту."""
        obj = self.current_item
        if not obj:
            return

        if hasattr(obj, 'title_bar') or hasattr(obj, 'resize_form'):
            if prop_name == "title":
                obj.title = str(value)
                if obj.scene():
                    obj.scene().update()
            elif prop_name == "x":
                try:
                    obj.setPos(float(value), obj.pos().y())
                    obj.update_handles_position()
                except:
                    pass
            elif prop_name == "y":
                try:
                    obj.setPos(obj.pos().x(), float(value))
                    obj.update_handles_position()
                except:
                    pass
            elif prop_name == "width":
                try:
                    obj.resize_form(float(value), obj.height)
                except:
                    pass
            elif prop_name == "height":
                try:
                    obj.resize_form(obj.width, float(value))
                except:
                    pass
            elif prop_name == "form_alias":
                obj.form_alias = str(value)
        else:
            if prop_name == "x":
                try:
                    pos = obj.pos()
                    obj.setPos(float(value), pos.y())
                except:
                    pass
            elif prop_name == "y":
                try:
                    pos = obj.pos()
                    obj.setPos(pos.x(), float(value))
                except:
                    pass
            elif prop_name == "width":
                try:
                    obj.setWidgetSize(float(value), obj.rect().height())
                except:
                    pass
            elif prop_name == "height":
                try:
                    obj.setWidgetSize(obj.rect().width(), float(value))
                except:
                    pass
            elif prop_name == "text":
                inner_w = obj.widget()
                if inner_w and hasattr(inner_w, 'setText'):
                    try:
                        inner_w.setText(str(value))
                    except:
                        pass
            elif prop_name == "objectName":
                inner_w = obj.widget()
                if inner_w:
                    inner_w.setObjectName(str(value))

