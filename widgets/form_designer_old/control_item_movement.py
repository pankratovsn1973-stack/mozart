# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item_movement.py

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsSceneMouseEvent
from .control_item_base import ControlItemBase


class ControlItemMovement(ControlItemBase):
    """Компонент графического контейнера, отвечающий за физический drag и ресайз на сцене."""

    def __init__(self, widget, control_id, control_type, parent=None):
        super().__init__(widget, control_id, control_type, parent)
        self._is_dragging = False
        self._drag_start_pos = QPointF()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.scenePos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Перемещение элемента или его хэндлов с защитой от ложного сдвига подконтролов."""
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.scenePos() - self._drag_start_pos
            self._drag_start_pos = event.scenePos()

            is_resize_mode = False
            if hasattr(self, '_resize_handle_active') and self._resize_handle_active:
                is_resize_mode = True
            elif hasattr(self.scene(), '_resize_mode_active') and self.scene()._resize_mode_active:
                is_resize_mode = True

            # Перемещение внутренних частей рефа блокируется в режиме изменения общих размеров
            if hasattr(self, '_active_child_item') and self._active_child_item and not is_resize_mode:
                child = self._active_child_item
                current_pos = child.pos()
                new_x = current_pos.x() + delta.x()
                new_y = current_pos.y() + delta.y()
                child.setPos(QPointF(new_x, new_y))
                child.updateGeometry()
            else:
                if is_resize_mode and hasattr(self, 'handle_resize_logic'):
                    self.handle_resize_logic(delta)
                else:
                    new_x = self.pos().x() + delta.x()
                    new_y = self.pos().y() + delta.y()
                    self.setPos(QPointF(new_x, new_y))

                if hasattr(self, 'geometry_changed') and hasattr(self, 'control_id'):
                    rect = self.rect()
                    self.geometry_changed.emit(
                        self.control_id,
                        int(self.pos().x()),
                        int(self.pos().y()),
                        int(rect.width()),
                        int(rect.height())
                    )

            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)
