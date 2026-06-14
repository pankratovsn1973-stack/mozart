# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_events_mixin.py

from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform

class EventsMixin:
    """Миксин: обработка кликов, перемещений, удаления."""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            items_to_delete = [item for item in self.controls.values() if item.is_selected]
            for item in items_to_delete:
                self.delete_control(item.control_id)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        clicked_item = self.itemAt(event.scenePos(), QTransform())
        if clicked_item is None or clicked_item == self.background:
            from PySide6.QtGui import QGuiApplication
            if not (QGuiApplication.keyboardModifiers() & Qt.ControlModifier):
                self.clear_selection()
                self.form_selected.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        for handle in self.control_handles:
            handle.update_position()