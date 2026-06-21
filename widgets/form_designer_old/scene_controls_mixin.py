# widgets/form_designer_old/scene_controls_mixin.py
# -*- coding: utf-8 -*-

import uuid
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QGuiApplication
from .control_item import ControlItem


class ControlsMixin:
    """Миксин: добавление, удаление, выделение контролов."""

    def _init_controls(self):
        self.controls = {}
        self.selected_control = None
        self.control_handles = []
        self.db = None

    def add_control(self, control_widget, control_id, control_type, x, y):
        """Добавляет контрол на сцену."""
        try:
            x = float(x) if x is not None else 50.0
            y = float(y) if y is not None else 50.0
        except (ValueError, TypeError):
            x = 50.0
            y = 50.0

        item = ControlItem(control_widget, control_id, control_type, parent=self.background)
        item.setPos(QPointF(x, y))

        item.selected_changed.connect(lambda sel: self._on_control_selected(item, sel))
        item.geometry_changed.connect(self._on_control_geometry_changed)

        self.controls[control_id] = item

        if hasattr(control_widget, 'set_design_mode'):
            control_widget.set_design_mode(True)

        if hasattr(self, 'control_added'):
            self.control_added.emit(item)

        return item

    def _on_control_selected(self, control_item, selected):
        """Обработчик выбора контрола — марштутизирует фокус в PropertyEditor."""
        if selected and control_item:
            self.selected_control = control_item
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(control_item)
        else:
            if len(self.selectedItems()) == 0:
                self.selected_control = None
                if hasattr(self, 'control_selected'):
                    self.control_selected.emit(None)

    def update_control_handles(self):
        """Обновляет позиции внутренних маркеров у всех выделенных контролов."""
        for item in self.selectedItems():
            if isinstance(item, ControlItem) and hasattr(item, 'update_handles_position'):
                item.update_handles_position()

    def _on_control_geometry_changed(self, control_id, x, y, width, height):
        """Обработчик изменения геометрии контрола."""
        try:
            # Шлем сигнал во все доступные слоты сцены для 100% прошивки связей
            if hasattr(self, 'geometry_changed'):
                self.geometry_changed.emit(
                    str(control_id), int(x), int(y), int(width), int(height)
                )
        except:
            pass

    def delete_control(self, control_id):
        """Безопасно удаляет контрол со сцены."""
        if control_id not in self.controls:
            return
        item = self.controls[control_id]

        if self.selected_control == item:
            self.selected_control = None
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

        if item and item.scene() == self:
            self.removeItem(item)

        del self.controls[control_id]
        if hasattr(self, 'control_deleted'):
            self.control_deleted.emit(str(control_id))

    def clear_selection(self):
        """Снимает выделение со всех элементов на сцене штатным методом Qt."""
        self.clearSelection()
        self.selected_control = None
        if hasattr(self, 'control_selected'):
            self.control_selected.emit(None)

    def focus_on_properties(self, control_item):
        """Фокусируется на свойствах конкретного контрола."""
        self.clear_selection()
        if control_item:
            control_item.setSelected(True)

    def get_controls_data(self):
        """Собирает данные всех контролов для сохранения в БД."""
        controls_list = []
        for control_id, item in self.controls.items():
            if not item:
                continue
            w = item.widget()
            if not w:
                continue

            props = {}
            if hasattr(w, 'properties') and isinstance(w.properties, dict):
                props.update(w.properties)

            pos = item.pos()
            props['x'] = int(float(pos.x()) if pos.x() is not None else 50)
            props['y'] = int(float(pos.y()) if pos.y() is not None else 50)

            rect = item.rect()
            props['width'] = int(rect.width()) if rect.width() > 0 else 150
            props['height'] = int(rect.height()) if rect.height() > 0 else 30

            controls_list.append({
                'id': str(control_id),
                'calias': w.objectName() if w else f"{item.control_type}_{control_id}",
                'cclass': item.control_type,
                'properties': props
            })
        return controls_list

    def load_controls(self, controls_data):
        """Загружает контролы из структуры метаданных."""
        if not controls_data:
            return

        from controls import create_control

        for data in controls_data:
            try:
                control_id = str(data.get('id', str(uuid.uuid4())[:8]))
                calias = data.get('calias', f"control_{control_id}")
                cclass = data.get('cclass', 'textbox')
                props = data.get('properties', {})

                x = props.pop('x', 50)
                y = props.pop('y', 50)
                width = props.pop('width', 150)
                height = props.pop('height', 30)

                x = int(float(x) if x is not None else 50)
                y = int(float(y) if y is not None else 50)
                width = int(float(width) if width is not None else 150)
                height = int(float(height) if height is not None else 30)

                widget = create_control(cclass, parent=None, db=self.db)
                if not widget:
                    continue

                widget.setObjectName(calias)
                if hasattr(widget, 'properties'):
                    widget.properties = props

                try:
                    widget.setFixedSize(width, height)
                except:
                    pass

                item = self.add_control(widget, control_id, cclass, x, y)
                if item:
                    item.updateGeometry()
                    if hasattr(item, 'update_handles_position'):
                        item.update_handles_position()

            except Exception as e:
                print(f"[ControlsMixin] Ошибка загрузки контрола: {e}")

    def update_control_property(self, control_id, prop_name, value):
        """Обновляет свойство контрола из инспектора."""
        if control_id not in self.controls:
            return
        item = self.controls[control_id]
        widget = item.widget()
        if not widget:
            return

        try:
            if hasattr(widget, 'properties') and isinstance(widget.properties, dict):
                widget.properties[prop_name] = value
            item.updateGeometry()
            if hasattr(item, 'update_handles_position'):
                item.update_handles_position()
        except Exception as e:
            print(f"[ControlsMixin] Ошибка обновления свойства: {e}")
