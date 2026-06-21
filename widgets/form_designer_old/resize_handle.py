# widgets/form_designer_old/resize_handle.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter


class ResizeHandle(QGraphicsRectItem):
    """Правый нижний маркер изменения размеров для формы бланка и контролов."""

    POSITIONS = {4: "BottomRight"}

    def __init__(self, position_index, target_item, parent=None):
        super().__init__(parent)
        self.target_item = target_item
        self.position_index = int(position_index)

        self.handle_size = 16.0
        self.setRect(-self.handle_size / 2, -self.handle_size / 2,
                     self.handle_size, self.handle_size)

        # Отключаем автоматическое перемещение Qt.
        # Маркер жестко привязан к форме/контролу и не накапливает ошибки двойного смещения.
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

        self.update_position()

    def update_position(self):
        if not self.target_item:
            return

        form_rect = self.target_item.rect()
        w = form_rect.width()
        h = form_rect.height()

        offset = 2.0
        x = w - offset
        y = h - offset

        self.setPos(QPointF(x, y))

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

            # Запоминаем исходные координаты объекта
            form_pos = self.target_item.pos()
            self.start_x = form_pos.x()
            self.start_y = form_pos.y()

            # Читаем ширину/высоту из свойств формы или из rect() контрола-прокси
            self.start_w = getattr(self.target_item, '_width', self.target_item.rect().width())
            self.start_h = getattr(self.target_item, '_height', self.target_item.rect().height())

            # Фиксируем клик в абсолютных координатах сцены один раз (ультрабыстро)
            self.start_mouse_scene = event.scenePos()

            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._is_resizing or not self.target_item:
            super().mouseMoveEvent(event)
            return

        # Считываем позицию мыши напрямую из сцены БЕЗ тяжелых вызовов mapToParent
        current_mouse_scene = event.scenePos()

        # Чистая математика вычитания двух векторов на сцене
        dx = current_mouse_scene.x() - self.start_mouse_scene.x()
        dy = current_mouse_scene.y() - self.start_mouse_scene.y()

        # Настраиваем минимальные пороги: для контролов лимиты компактнее (20x20)
        is_form = hasattr(self.target_item, 'update_geometry')
        min_w = 50.0 if is_form else 20.0
        min_h = 50.0 if is_form else 20.0

        new_w = max(min_w, self.start_w + dx)
        new_h = max(min_h, self.start_h + dy)

        if is_form:
            # ВЕТКА ФОРМЫ (FormBackground)
            self.target_item.update_geometry(
                self.start_x,
                self.start_y,
                new_w,
                new_h
            )
        else:
            # ВЕТКА КОНТРОЛА (ControlItem)
            if hasattr(self.target_item, 'setWidgetSize'):
                self.target_item.setWidgetSize(new_w, new_h)

        self.update_position()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = False
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

        # Рисуем декоративные насечки в углу маркера
        painter.setPen(QPen(QColor('#888888'), 1.0, Qt.PenStyle.SolidLine))
        painter.drawLine(rect.left() + 3, rect.bottom() - 3,
                         rect.right() - 3, rect.top() + 3)
        painter.drawLine(rect.left() + 6, rect.bottom() - 3,
                         rect.right() - 3, rect.top() + 6)

        painter.restore()
