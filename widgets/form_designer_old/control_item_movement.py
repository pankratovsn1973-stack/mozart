# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item_movement.py

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent


class ControlItemMovement:
    """Миксин состояния для перемещения контролов по сцене."""

    def __init__(self, widget, control_id, control_type, parent=None):
        # ✅ ИСПРАВЛЕНИЕ: НЕ вызываем super().__init__(parent), так как это миксин
        self._is_dragging = False
        self._drag_start_pos = QPointF()
        self.control_id = str(control_id).strip()
        self.control_type = control_type

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            # Запоминаем смещение мыши относительно позиции элемента
            self._drag_start_pos = event.scenePos() - self.pos()
            return

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self._is_dragging:
            return

        # ✅ Перемещаем САМ ПРОКСИ (ControlItem)
        new_pos = event.scenePos() - self._drag_start_pos
        self.setPos(new_pos)

        # ✅ КРИТИЧЕСКИЙ ФИКС: Обновляем позицию маркера при каждом движении!
        # Так как маркер независимый (parent=None), он не двигается сам.
        if hasattr(self, 'update_handles_position'):
            self.update_handles_position()

        # Уведомляем сцену об изменении геометрии
        if hasattr(self, 'geometry_changed'):
            rect = self.rect()
            self.geometry_changed.emit(
                self.control_id,
                int(new_pos.x()),
                int(new_pos.y()),
                int(rect.width()),
                int(rect.height())
            )

        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            event.accept()
            return