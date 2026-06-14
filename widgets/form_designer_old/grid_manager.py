# widgets/form_designer_old/grid_manager.py
# -*- coding: utf-8 -*-

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor


class GridManager:
    """Управление координатной сеткой с динамическим размером клетки"""

    def __init__(self, grid_size=10):
        self._grid_size = grid_size
        self.snap_enabled = True
        self.visible = True

    @property
    def grid_size(self):
        return self._grid_size

    @grid_size.setter
    def grid_size(self, value):
        # Ограничиваем размер клетки от 4 до 100 пикселей для стабильности
        self._grid_size = max(4, min(100, int(value)))

    def snap(self, point, origin=QPointF(0, 0)):
        """Привязывает точку к динамической сетке"""
        if not self.snap_enabled:
            return point

        x = round((point.x() - origin.x()) / self._grid_size) * self._grid_size + origin.x()
        y = round((point.y() - origin.y()) / self._grid_size) * self._grid_size + origin.y()
        return QPointF(x, y)

    def draw(self, painter: QPainter, rect, origin):
        """Рисует координатную сетку строго внутри границ бланка формы"""
        if not self.visible:
            return

        painter.save()

        # Настройка пера: для мелкой клетки делаем линии прозрачнее, чтобы не рябило
        alpha = 70 if self._grid_size < 10 else 120
        pen_style = Qt.DotLine if self._grid_size < 15 else Qt.SolidLine
        painter.setPen(QPen(QColor(180, 180, 180, alpha), 0.5, pen_style))

        # Обрезаем холст строго по границам переданного прямоугольника бланка формы
        painter.setClipRect(rect)

        # Вычисляем физические границы бланка формы на сцене
        left = int(rect.left())
        top = int(rect.top())
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Корректный расчет стартового шага относительно верхнего левого угла (origin) формы
        # Проходим циклом по всей ширине формы от left до right
        x = left + self._grid_size
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += self._grid_size

        # Проходим циклом по всей высоте формы от top до bottom
        y = top + self._grid_size
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += self._grid_size

        painter.restore()

    def toggle_visible(self):
        self.visible = not self.visible
        return self.visible

    def toggle_snap(self):
        self.snap_enabled = not self.snap_enabled
        return self.snap_enabled
