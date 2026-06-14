# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/property_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QPushButton, QLabel, QDialog, QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal

from lang.local_translator import LocalTranslator
from .property_inspector import PropertyInspector
from .property_helpers import safe_get_width, safe_get_height


class PropertyEditor(QWidget):
    property_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.current_object = None
        self.current_object_type = None
        self.current_control_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self.translator.tr('properties_title'))
        self.title.setStyleSheet("font-weight: bold; padding: 5px; background-color: #e0e0e0;")
        layout.addWidget(self.title)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.translator.tr('property'), self.translator.tr('value')])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._edit_property)
        layout.addWidget(self.table)

        self.btn_add = QPushButton(self.translator.tr('property_add'))
        self.btn_add.clicked.connect(self._add_property)
        layout.addWidget(self.btn_add)

    def set_control(self, control_item):
        self.current_object = control_item if (control_item and hasattr(control_item, 'control_widget')) else None
        self.current_object_type = 'control' if self.current_object else None
        self.current_control_id = control_item.control_id if control_item else None
        self._load_properties()

    def set_form(self, form_object):
        if form_object and hasattr(form_object, '_runtime_form'):
            self.current_object = form_object._runtime_form
        else:
            self.current_object = form_object
        self.current_object_type = 'form'
        self.current_control_id = None
        self._load_properties()

    def update_geometry_values(self, x, y, width, height):
        if self.current_object_type != 'control':
            return
        for row in range(self.table.rowCount()):
            prop_item = self.table.item(row, 0)
            if not prop_item:
                continue
            prop_name = prop_item.text().lower()
            if 'x' in prop_name and ('коорд' in prop_name or 'x' == prop_name):
                self.table.item(row, 1).setText(str(x))
            elif 'y' in prop_name and ('коорд' in prop_name or 'y' == prop_name):
                self.table.item(row, 1).setText(str(y))
            elif 'ширин' in prop_name or 'width' in prop_name:
                self.table.item(row, 1).setText(str(width))
            elif 'высот' in prop_name or 'height' in prop_name:
                self.table.item(row, 1).setText(str(height))

    def _get_target_widget(self):
        if self.current_object_type == 'control' and self.current_object:
            return self.current_object.control_widget
        elif self.current_object_type == 'form':
            return self.current_object
        return None

    def _load_properties(self):
        self.table.setRowCount(0)
        if not self.current_object:
            self.title.setText("Свойства")
            return

        target_obj = self._get_target_widget()

        if self.current_object_type == 'form':
            self.title.setText("Свойства: Бизнес-форма")
            self._load_form_properties()
        else:
            self.title.setText(f"Свойства: {self.current_object.control_type}")
            self._add_row("X Координата", int(self.current_object.pos().x()), "int", "x")
            self._add_row("Y Координата", int(self.current_object.pos().y()), "int", "y")
            if target_obj is not None:
                self._add_row("Ширина элемента", int(safe_get_width(target_obj)), "int", "width")
                self._add_row("Высота элемента", int(safe_get_height(target_obj)), "int", "height")
            self._load_control_properties()

        all_props = PropertyInspector.inspect(target_obj)
        for tech_name, (display_name, value, prop_type) in all_props.items():
            if tech_name not in ('binding_field', 'entity_alias', 'is_required', 'placeholderText', 'text', 'readOnly',
                                 'label', 'x', 'y', 'width', 'height'):
                self._add_row(display_name, value, prop_type, tech_name)

    def _load_form_properties(self):
        obj = self.current_object
        self._add_row("Заголовок формы", getattr(obj, 'title', getattr(obj, '_title', 'Форма')), "str", "title")
        self._add_row("Алиас формы", getattr(obj, 'form_alias', getattr(obj, '_form_alias', '')), "str", "form_alias")
        self._add_row("Алиас сущности", getattr(obj, 'entity_alias', getattr(obj, '_entity_alias', '')), "str", "entity_alias")
        self._add_row("Идентификатор", str(getattr(obj, 'instance_id', getattr(obj, '_instance_id', '')) or ""), "str", "instance_id")
        self._add_row("Только чтение", bool(getattr(obj, 'readonly', getattr(obj, '_readonly', False))), "bool", "readonly")

        bg = getattr(obj, '_design_background', None)
        if not bg and hasattr(obj, 'parentWidget') and obj.parentWidget():
            parent = obj.parentWidget()
            if hasattr(parent, 'scene') and parent.scene() and hasattr(parent.scene(), 'background'):
                bg = parent.scene().background
        if bg:
            self._add_row("Ширина формы", int(bg.width), "int", "width")
            self._add_row("Высота формы", int(bg.height), "int", "height")

    def _load_control_properties(self):
        control = self.current_object.control_widget
        c_type = self.current_object.control_type

        self._add_row("Имя (Алиас)", control.objectName(), "str", "objectName")
        self._add_row("Поле привязки", getattr(control, 'binding_field', ''), "str", "binding_field")
        self._add_row("Алиас сущности", getattr(control, 'entity_alias', ''), "str", "entity_alias")
        self._add_row("Обязательное", bool(getattr(control, 'is_required', False)), "bool", "is_required")

        label = ""
        if hasattr(control, 'placeholderText'):
            label = control.placeholderText()
        elif hasattr(control, 'text') and c_type in ('checkbox', 'radiobutton'):
            label = control.text()
        else:
            label = getattr(control, '_label', '')
        self._add_row("Текст / Подпись", label, "str", "label")

        if hasattr(control, 'isReadOnly'):
            self._add_row("Только для чтения", control.isReadOnly(), "bool", "readOnly")

        if c_type == 'numberbox':
            self._add_row("Мин. значение", getattr(control, 'min_value', 0.0), "float", "min_value")
            self._add_row("Макс. значение", getattr(control, 'max_value', 999999999.0), "float", "max_value")
            self._add_row("Знаков после запятой", getattr(control, 'decimal_places', 2), "int", "decimal_places")

        if c_type in ('combobox', 'listbox', 'optiongroup'):
            self._add_row("Пункты списка", getattr(control, 'items_json', '[]'), "str", "items_json")

    def _add_row(self, display_name, value, prop_type="str", internal_name=""):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.data(Qt.UserRole) == internal_name:
                item.setText(str(value) if value is not None else "")
                return
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(display_name))
        value_item = QTableWidgetItem(str(value) if value is not None else "")
        value_item.setData(Qt.UserRole, internal_name)
        value_item.setData(Qt.UserRole + 1, prop_type)
        self.table.setItem(row, 1, value_item)

    def _edit_property(self, item):
        if item.column() != 1:
            return
        prop_name = item.data(Qt.UserRole)
        prop_type = item.data(Qt.UserRole + 1)
        current_value = item.text()

        if prop_type == 'bool':
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Изменить {prop_name}")
            layout = QVBoxLayout(dlg)
            cb = QCheckBox()
            cb.setChecked(current_value.lower() == 'true')
            layout.addWidget(cb)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dlg.accept)
            btn_box.rejected.connect(dlg.reject)
            layout.addWidget(btn_box)
            if dlg.exec():
                new_value = cb.isChecked()
                item.setText(str(new_value))
                self.property_changed.emit(prop_name, new_value)
        elif prop_type in ('int', 'float'):
            new_value, ok = QInputDialog.getText(self, f"Изменить {prop_name}", "Новое значение:", text=current_value)
            if ok:
                try:
                    new_value = int(new_value) if prop_type == 'int' else float(new_value)
                    item.setText(str(new_value))
                    self.property_changed.emit(prop_name, new_value)
                except:
                    pass
        else:
            new_value, ok = QInputDialog.getText(self, f"Изменить {prop_name}", "Новое значение:", text=current_value)
            if ok:
                item.setText(new_value)
                self.property_changed.emit(prop_name, new_value)

    def _add_property(self):
        prop_name, ok = QInputDialog.getText(self, "Новое свойство", "Имя пользовательского свойства:")
        if ok and prop_name:
            self._add_row(prop_name, "", "str", prop_name)