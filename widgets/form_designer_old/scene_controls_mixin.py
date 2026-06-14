# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_controls_mixin.py

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QGuiApplication, QTransform
from .control_item import ControlItem
from .resize_handle import ResizeHandle


class ControlsMixin:
    """Миксин: добавление, удаление, выделение контролов, сохранение данных."""

    def _init_controls(self):
        pass

    def add_control(self, control_widget, control_id, control_type, x, y):
        item = ControlItem(control_widget, control_id, control_type, parent=self.background)
        item.setPos(QPointF(x, y))
        item.selected_changed.connect(self._on_control_selected)
        item.geometry_changed.connect(self._on_control_geometry_changed)
        self.controls[control_id] = item

        if hasattr(control_widget, 'set_design_mode'):
            control_widget.set_design_mode(True)
        return item

    def _on_control_selected(self, control, selected):
        for handle in self.control_handles:
            if handle.scene():
                self.removeItem(handle)
        self.control_handles.clear()

        if selected:
            if self.selected_control and self.selected_control != control:
                if not (QGuiApplication.keyboardModifiers() & Qt.ControlModifier):
                    self.selected_control.set_selected(False)
            self.selected_control = control
            for pos_key in ResizeHandle.POSITIONS.keys():
                handle = ResizeHandle(pos_key, control)
                self.control_handles.append(handle)
                handle.update_position()
            self.control_selected.emit(control)
        else:
            if self.selected_control == control:
                self.selected_control = None
                self.control_selected.emit(None)

    def _on_control_geometry_changed(self, control_id, x, y, width, height):
        self.geometry_changed.emit(control_id, x, y, width, height)

    def delete_control(self, control_id):
        if control_id not in self.controls:
            return
        item = self.controls[control_id]
        if self.selected_control == item:
            for handle in self.control_handles:
                if handle.scene():
                    self.removeItem(handle)
            self.control_handles.clear()
            self.selected_control = None
            self.control_selected.emit(None)
        if item.scene():
            self.removeItem(item)
        del self.controls[control_id]
        if self.background and self.background.status_bar:
            self.background.status_bar.show_message(f"Удален компонент: {control_id}")

    def clear_selection(self):
        for item in list(self.controls.values()):
            item.set_selected(False)
            item.setSelected(False)
        for handle in self.control_handles:
            if handle.scene():
                self.removeItem(handle)
        self.control_handles.clear()
        self.selected_control = None

    def focus_on_properties(self, control_item):
        self.clear_selection()
        control_item.set_selected(True)

    def get_controls_data(self):
        controls_list = []
        for control_id, item in self.controls.items():
            w = item.widget()
            props = {}
            if hasattr(w, 'properties') and isinstance(w.properties, dict):
                props.update(w.properties)
            props['x'] = int(item.pos().x())
            props['y'] = int(item.pos().y())

            if w and hasattr(w, 'width') and not callable(w.width):
                props['width'] = w.width
            else:
                props['width'] = 150
            if w and hasattr(w, 'height') and not callable(w.height):
                props['height'] = w.height
            else:
                props['height'] = 30

            controls_list.append({
                'id': control_id,
                'calias': w.objectName() if w else f"{item.control_type}_{control_id}",
                'cclass': item.control_type,
                'properties': props
            })
        return controls_list