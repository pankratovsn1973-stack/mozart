# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/resize_handle.py

from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QCursor


class ResizeHandle(QGraphicsRectItem):
    HANDLE_SIZE = 6
    HANDLE_OFFSET = HANDLE_SIZE // 2

    POSITIONS = {
        'tl': (0, 0, Qt.SizeFDiagCursor),
        'tr': (1, 0, Qt.SizeBDiagCursor),
        'bl': (0, 1, Qt.SizeBDiagCursor),
        'br': (1, 1, Qt.SizeFDiagCursor),
        't': (0.5, 0, Qt.SizeVerCursor),
        'b': (0.5, 1, Qt.SizeVerCursor),
        'l': (0, 0.5, Qt.SizeHorCursor),
        'r': (1, 0.5, Qt.SizeHorCursor),
    }

    def __init__(self, position, target_item, parent=None):
        super().__init__(target_item)
        self.position = position
        self.target_item = target_item
        self._resizing = False
        self._start_rect = None
        self._start_pos = None
        self._start_target_pos = None

        self.setRect(-self.HANDLE_OFFSET, -self.HANDLE_OFFSET,
                     self.HANDLE_SIZE, self.HANDLE_SIZE)
        self.setBrush(QBrush(QColor(0, 120, 215)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setZValue(2000)

        cursor = self.POSITIONS[position][2]
        self.setCursor(QCursor(cursor))

    def _get_target_size(self):
        """Безопасно возвращает (width, height) целевого объекта."""
        # Для ControlItem
        if hasattr(self.target_item, 'control_widget') and self.target_item.control_widget:
            cw = self.target_item.control_widget
            if hasattr(cw, 'width'):
                if callable(cw.width):
                    try:
                        w = cw.width()
                    except:
                        w = 100
                else:
                    w = cw.width
            else:
                w = 100

            if hasattr(cw, 'height'):
                if callable(cw.height):
                    try:
                        h = cw.height()
                    except:
                        h = 30
                else:
                    h = cw.height
            else:
                h = 30
            return w, h

        # Для FormBackground
        if hasattr(self.target_item, 'rect'):
            rect = self.target_item.rect()
            return rect.width(), rect.height()

        return 100, 100

    def update_position(self):
        if not self.target_item:
            return
        w, h = self._get_target_size()
        rel_x, rel_y, _ = self.POSITIONS[self.position]
        x = w * rel_x
        y = h * rel_y
        self.setPos(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            w, h = self._get_target_size()
            self._start_rect = QRectF(0, 0, w, h)
            self._start_pos = event.scenePos()
            self._start_target_pos = self.target_item.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            scene_pos = event.scenePos()
            if self.target_item.scene() and hasattr(self.target_item.scene(), 'snap_point'):
                scene_pos = self.target_item.scene().snap_point(scene_pos)

            delta = scene_pos - self._start_pos

            old_w = self._start_rect.width()
            old_h = self._start_rect.height()

            is_control = hasattr(self.target_item, 'control_widget')
            min_w = 20 if is_control else 400
            min_h = 20 if is_control else 200

            new_w = old_w
            new_h = old_h
            offset_x = 0.0
            offset_y = 0.0

            if self.position in ('r', 'tr', 'br'):
                new_w = max(min_w, old_w + delta.x())
            if self.position in ('l', 'tl', 'bl'):
                max_delta_x = old_w - min_w
                actual_delta_x = min(delta.x(), max_delta_x)
                new_w = old_w - actual_delta_x
                offset_x = actual_delta_x

            if self.position in ('b', 'bl', 'br'):
                new_h = max(min_h, old_h + delta.y())
            if self.position in ('t', 'tl', 'tr'):
                max_delta_y = old_h - min_h
                actual_delta_y = min(delta.y(), max_delta_y)
                new_h = old_h - actual_delta_y
                offset_y = actual_delta_y

            if is_control:
                widget = self.target_item.widget()
                if widget:
                    widget.resize(int(new_w), int(new_h))
                self.target_item.setGeometry(0, 0, int(new_w), int(new_h))
                if hasattr(self.target_item, '_emit_geometry'):
                    self.target_item._emit_geometry()
            else:
                if hasattr(self.target_item, 'set_size'):
                    self.target_item.set_size(new_w, new_h)
                elif hasattr(self.target_item, 'setRect'):
                    self.target_item.setRect(0, 0, new_w, new_h)

            new_pos = self._start_target_pos + QPointF(offset_x, offset_y)
            self.target_item.setPos(new_pos)

            if is_control:
                self.update_control_handles()
            else:
                if self.target_item.scene() and hasattr(self.target_item.scene(), 'update_resize_handles_position'):
                    self.target_item.scene().update_resize_handles_position()

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def update_control_handles(self):
        scene = self.target_item.scene()
        if scene and hasattr(scene, 'control_handles'):
            for handle in scene.control_handles:
                handle.update_position()

    def mouseReleaseEvent(self, event):
        self._resizing = False
        event.accept()