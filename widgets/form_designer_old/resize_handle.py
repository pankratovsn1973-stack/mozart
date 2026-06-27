# widgets/form_designer_old/resize_handle.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter


class ResizeHandle(QGraphicsRectItem):
    """Интеллектуальный маркер ресайза, поддерживающий групповой синхронный шаг изменений."""

    POSITIONS = {4: "BottomRight"}

    def __init__(self, position_index, target_item, parent=None):
        super().__init__(parent)
        self.target_item = target_item
        self.position_index = int(position_index)

        self.handle_size = 16.0
        self.setRect(-self.handle_size / 2, -self.handle_size / 2, self.handle_size, self.handle_size)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)
        self.setZValue(100)

        self.setPen(QPen(QColor('#0066ff'), 2.0, Qt.PenStyle.SolidLine))
        self.setBrush(QColor('#ffffff'))

        self._hovered = False
        self._normal_color = QColor('#0066ff')
        self._hover_color = QColor('#ff5500')

        self._is_resizing = False
        self.start_x = 0.0
        self.start_y = 0.0
        self.start_w = 0.0
        self.start_h = 0.0
        self.start_mouse_scene = QPointF()

        # Словарь для хранения начальных размеров всей выделенной группы (как под-контролов, так и контейнеров)
        self._start_group_sizes = {}

    def update_position(self):
        """Прямой расчет координат маркера без обратного вызова родительских методов."""
        if not self.target_item:
            return

        child_widget = getattr(self.target_item, '_focused_child_widget', None)
        if child_widget:
            child_geo = child_widget.geometry()
            offset = 2.0
            x = float(child_geo.right() - offset)
            y = float(child_geo.bottom() - offset)
            self.setPos(QPointF(x, y))
            return

        try:
            form_rect = self.target_item.rect()
            w = form_rect.width()
            h = form_rect.height()
        except:
            w = getattr(self.target_item, '_width', 150.0)
            h = getattr(self.target_item, '_height', 30.0)

        offset = 2.0
        self.setPos(QPointF(w - offset, h - offset))

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.setPen(QPen(self._hover_color, 2.5, Qt.PenStyle.SolidLine))
        self.update()
        event.accept()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.setPen(QPen(self._normal_color, 2.0, Qt.PenStyle.SolidLine))
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            self._start_group_sizes.clear()

            form_pos = self.target_item.pos()
            self.start_x = form_pos.x()
            self.start_y = form_pos.y()

            child_widget = getattr(self.target_item, '_focused_child_widget', None)
            if child_widget:
                # ВЕТКА А: Фиксируем размеры внутренностей (если мы в каскадном режиме)
                self.start_w = float(child_widget.width())
                self.start_h = float(child_widget.height())
                if hasattr(self.target_item, 'get_start_child_sizes'):
                    self._start_group_sizes = self.target_item.get_start_child_sizes()
            else:
                # ВЕТКА Б: Режим верхнего уровня (ресайзим внешние ControlItem)
                self.start_w = getattr(self.target_item, '_width', self.target_item.rect().width())
                self.start_h = getattr(self.target_item, '_height', self.target_item.rect().height())

                # ИСПРАВЛЕНО: Запоминаем исходные размеры ВСЕХ выделенных объектов на сцене
                if self.scene():
                    from .control_item_base import ControlItemBase
                    for item in self.scene().selectedItems():
                        if isinstance(item, ControlItemBase):
                            # Сохраняем (ширину, высоту) каждого прокси из его rect()
                            self._start_group_sizes[item] = (float(item.rect().width()), float(item.rect().height()))

            self.start_mouse_scene = event.scenePos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self._is_resizing or not self.target_item:
            super().mouseMoveEvent(event)
            return

        current_mouse_scene = event.scenePos()
        dx = current_mouse_scene.x() - self.start_mouse_scene.x()
        dy = current_mouse_scene.y() - self.start_mouse_scene.y()

        is_form = hasattr(self.target_item, 'update_geometry')

        if is_form:
            self.target_item.update_geometry(self.start_x, self.start_y, max(50.0, self.start_w + dx),
                                             max(50.0, self.start_h + dy))
        else:
            child_widget = getattr(self.target_item, '_focused_child_widget', None)

            if child_widget:
                # 1. Групповой ресайз внутренних элементов в изолированном контексте
                if self._start_group_sizes:
                    for child, (orig_w, orig_h) in self._start_group_sizes.items():
                        new_w = max(20.0, orig_w + dx)
                        new_h = max(15.0, orig_h + dy)
                        child.setFixedSize(int(new_w), int(new_h))
                else:
                    new_w = max(20.0, self.start_w + dx)
                    new_h = max(15.0, self.start_h + dy)
                    child_widget.setFixedSize(int(new_w), int(new_h))
            else:
                # 2. ИСПРАВЛЕНО: Групповой синхронный ресайз внешних ControlItem на сцене
                from .control_item_base import ControlItemBase
                has_group = len([i for i in self._start_group_sizes.keys() if isinstance(i, ControlItemBase)]) > 1

                if has_group:
                    for item, (orig_w, orig_h) in self._start_group_sizes.items():
                        new_w = max(20.0, orig_w + dx)
                        new_h = max(20.0, orig_h + dy)
                        if hasattr(item, 'setWidgetSize'):
                            item.setWidgetSize(new_w, new_h)
                else:
                    # Одиночный ресайз одного выбранного контейнера
                    new_w = max(20.0, self.start_w + dx)
                    new_h = max(20.0, self.start_h + dy)
                    if hasattr(self.target_item, 'setWidgetSize'):
                        self.target_item.setWidgetSize(new_w, new_h)

        self.update_position()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = False
            self._start_group_sizes.clear()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, 3, 3)

        painter.setPen(QPen(QColor('#888888'), 1.0, Qt.PenStyle.SolidLine))
        painter.drawLine(rect.left() + 3, rect.bottom() - 3, rect.right() - 3, rect.top() + 3)
        painter.drawLine(rect.left() + 6, rect.bottom() - 3, rect.right() - 3, rect.top() + 6)

        painter.restore()
