# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_events_mixin.py

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from PySide6.QtGui import QKeyEvent
from .control_item_base import ControlItemBase
from .focus_registry import FocusRegistry


class EventsMixin:
    """Миксин сцены, управляющий контекстным фокусом по изменению коллекции выделения."""

    def _init_context_metadata(self):
        self._active_context_container = None
        self.selectionChanged.connect(self._on_global_selection_changed)

    def _on_global_selection_changed(self):
        """Программный перехват опустевшей коллекции выделения."""
        selected_items = [i for i in self.selectedItems() if isinstance(i, ControlItemBase)]

        # Если коллекция стала абсолютно пустой (пользователь кликнул на сетку)
        if len(selected_items) == 0:
            self._active_context_container = None
            FocusRegistry().reset_active_context()
            self.setFocusItem(None)

            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            view_list = self.views()
            if view_list and view_list.__getitem__(0):
                view_list.__getitem__(0).setFocus()

            view_transform = view_list.transform() if view_list else None
            item = self.itemAt(event.scenePos(), view_transform or "")

            target_control = None
            if isinstance(item, ControlItemBase):
                target_control = item
            elif item and item.parentItem() and isinstance(item.parentItem(), ControlItemBase):
                target_control = item.parentItem()

            if target_control:
                self.setFocusItem(target_control)

                if self._active_context_container and self._active_context_container != target_control:
                    FocusRegistry().reset_active_context()
                    self._active_context_container = None

                if self._active_context_container and self._active_context_container == target_control:
                    target_control.mousePressEvent(event)
                    return

                selected_now = [i for i in self.selectedItems() if isinstance(i, ControlItemBase)]
                if len(selected_now) > 1 and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    if target_control in selected_now:
                        self.clearSelection()
                        target_control.setSelected(True)
                        if hasattr(self, 'select_control'):
                            self.select_control(target_control)
                        event.accept()
                        return

                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    if not self._active_context_container:
                        target_control.setSelected(not target_control.isSelected())
                    event.accept()
                    return

                if not target_control.isSelected():
                    FocusRegistry().reset_active_context()
                    self.clearSelection()
                    target_control.setSelected(True)
                    self._active_context_container = target_control

                    if hasattr(self, 'select_control'):
                        self.select_control(target_control)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)
        if hasattr(self, 'background') and self.background:
            local_form_pos = self.background.mapFromScene(event.scenePos())
            if hasattr(self.background, 'status_bar') and self.background.status_bar:
                sb = self.background.status_bar
                if hasattr(sb, 'set_coordinates'):
                    sb.set_coordinates(local_form_pos.x(), local_form_pos.y())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(event)
        if self._active_context_container:
            return
        selected = self.selectedItems()
        if hasattr(self, 'select_control'):
            if len(selected) == 1:
                self.select_control(selected)
