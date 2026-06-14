# widgets/form_designer_old/resize_handle.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс ResizeHandle (наследник QGraphicsRectItem).
Описывает поведение отдельных "волшебных точек" изменения размера объектов на холсте.
Исправлен порядок аргументов в __init__ для полного соответствия вызову в form_scene.py.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter


class ResizeHandle(QGraphicsRectItem):
    """
    Класс отдельного управляющего маркера (волшебной точки).
    Отвечает за физическое изменение размеров родительского объекта мышью.
    """

    # Статический словарь позиций для совместимости с циклом инициализации в form_scene.py
    POSITIONS = {
        0: "TopLeft",
        1: "TopMid",
        2: "TopRight",
        3: "RightMid",
        4: "BottomRight",
        5: "BottomMid",
        6: "BottomLeft",
        7: "LeftMid"
    }

    def __init__(self, position_index, target_item, parent=None):
        # ИСПРАВЛЕНО: Порядок аргументов изменен на (position_index, target_item) под строку 47 в form_scene.py
        super().__init__(parent)
        self.target_item = target_item
        self.position_index = int(position_index)

        self.handle_size = 7.0
        self.setRect(-self.handle_size / 2, -self.handle_size / 2, self.handle_size, self.handle_size)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)

        self.setPen(QPen(QColor('#0055ff'), 1, Qt.SolidLine))
        self.setBrush(QColor('#ffffff'))

        self._is_resizing = False
        self._drag_start_pos = QPointF()
        self._start_target_rect = QRectF()

        self.update_position()

    def update_position(self):
        """Раскладывает квадратики строго по углам и сторонам прямоугольника формы/контрола."""
        if not self.target_item:
            return

        t_rect = self.target_item.rect()
        t_pos = self.target_item.pos()

        w, h = t_rect.width(), t_rect.height()
        mid_x, mid_y = w / 2.0, h / 2.0

        # Массив точек привязки маркеров к геометрии объекта
        points = [
            QPointF(0.0, 0.0),  # 0: TopLeft
            QPointF(mid_x, 0.0),  # 1: TopMid
            QPointF(w, 0.0),  # 2: TopRight
            QPointF(w, mid_y),  # 3: RightMid
            QPointF(w, h),  # 4: BottomRight
            QPointF(mid_x, h),  # 5: BottomMid
            QPointF(0.0, h),  # 6: BottomLeft
            QPointF(0.0, mid_y)  # 7: LeftMid
        ]

        if 0 <= self.position_index < len(points):
            # Сдвигаем маркер в координаты сцены относительно текущего положения объекта
            self.setPos(t_pos + points[self.position_index])

    def mousePressEvent(self, event):
        """Фиксация стартовых параметров перед началом изменения размеров."""
        if event.button() == Qt.LeftButton:
            self._is_resizing = True
            self._drag_start_pos = event.scenePos()
            self._start_target_rect = self.target_item.rect()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Математический алгоритм изменения размеров формы/контрола по осям."""
        if not self._is_resizing or not self.target_item:
            super().mouseMoveEvent(event)
            return

        delta = event.scenePos() - self._drag_start_pos

        # Если у сцены включен Snap, округляем дельту сдвига до шага сетки
        if self.scene() and hasattr(self.scene(), 'snap_to_grid'):
            snapped_pos = self.scene().snap_to_grid(self.pos() + delta)
            delta = snapped_pos - self.pos()

        w = self._start_target_rect.width()
        h = self._start_target_rect.height()

        new_w, new_h = w, h

        # Алгоритм FoxPro: Вычисляем новые размеры в зависимости от индекса потянутой точки
        if self.position_index == 2:  # TopRight
            new_w = w + delta.x()
        elif self.position_index == 3:  # RightMid
            new_w = w + delta.x()
        elif self.position_index == 4:  # BottomRight
            new_w = w + delta.x()
            new_h = h + delta.y()
        elif self.position_index == 5:  # BottomMid
            new_h = h + delta.y()
        elif self.position_index == 6:  # BottomLeft
            new_h = h + delta.y()

        # Защита от схлопывания в отрицательный размер
        new_w = max(50.0, new_w)
        new_h = max(50.0, new_h)

        # Дёргаем метод ресайза у подложки формы или контрола
        if hasattr(self.target_item, 'resize_form'):
            self.target_item.resize_form(new_w, new_h)

        event.accept()

    def mouseReleaseEvent(self, event):
        """Завершение цикла изменения размеров."""
        if event.button() == Qt.LeftButton:
            self._is_resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        """Отрисовка синих квадратиков-маркеров."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())
        painter.restore()
