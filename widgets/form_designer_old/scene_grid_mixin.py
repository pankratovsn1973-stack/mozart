# widgets/form_designer_old/scene_grid_mixin.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс-примесь EventsMixin для FormDesignerScene.
Управляет координатной сеткой и привязкой (Snap) элементов.
Интегрирован со всеми кнопками управления из main_widget.py.
"""

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene


class GridMixin:
    """Миксин управления сеткой холста формы."""

    def _init_grid(self):
        """Инициализация дефолтных параметров отображения сетки."""
        self._grid_visible = True
        self._snap_enabled = True
        self._grid_size = 10
        self._grid_color = QColor('#d0d0d0')
        self._scene_bg_color = QColor('#e8e8e8')
        self._form_bg_color = QColor('#ffffff')

    def set_grid_visible(self, visible: bool):
        """Включает/выключает отображение линий сетки."""
        self._grid_visible = visible
        self._refresh_grid_layers()

    def set_snap_enabled(self, enabled: bool):
        """
        ИСПРАВЛЕНО: Метод вызывается из main_widget.py при клике на кнопку 'Привязка'.
        """
        self._snap_enabled = enabled

    def set_grid_size(self, size: int):
        """
        ИСПРАВЛЕНО: Метод вызывается из main_widget.py при изменении шага сетки.
        """
        self._grid_size = max(2, size)
        self._refresh_grid_layers()

    def _refresh_grid_layers(self):
        """Принудительно заставляет Qt перерисовать слои переднего и заднего плана."""
        if hasattr(self, 'invalidate') and hasattr(self, 'sceneRect'):
            self.invalidate(self.sceneRect(), QGraphicsScene.BackgroundLayer | QGraphicsScene.ForegroundLayer)

    def snap_to_grid(self, pos: QPointF) -> QPointF:
        """Математическое округление координат до ближайшего шага сетки."""
        if not getattr(self, '_snap_enabled', True) or self._grid_size <= 1:
            return pos
        x = round(pos.x() / self._grid_size) * self._grid_size
        y = round(pos.y() / self._grid_size) * self._grid_size
        return QPointF(max(0.0, x), max(0.0, y))

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Заливка внешнего пространства сцены серым цветом окружения."""
        painter.fillRect(rect, getattr(self, '_scene_bg_color', QColor('#e8e8e8')))

        # Если форма (background) существует, красим её подложку в белый цвет
        form_item = getattr(self, 'background', None)
        if form_item:
            painter.save()
            painter.setTransform(form_item.sceneTransform(), True)
            painter.fillRect(form_item.rect(), getattr(self, '_form_bg_color', QColor('#ffffff')))
            painter.restore()

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """Гарантированная отрисовка линий сетки строго поверх контура белой формы."""
        super().drawForeground(painter, rect)
        if not getattr(self, '_grid_visible', True):
            return

        form_item = getattr(self, 'background', None)
        if not form_item:
            return

        painter.save()
        painter.setTransform(form_item.sceneTransform(), True)
        f_rect = form_item.rect()

        grid_pen = QPen(getattr(self, '_grid_color', QColor('#d0d0d0')), 1, Qt.SolidLine)
        painter.setPen(grid_pen)

        step = self._grid_size
        left, top = int(f_rect.left()), int(f_rect.top())
        right, bottom = int(f_rect.right()), int(f_rect.bottom())

        for x in range(left + step, right, step):
            painter.drawLine(x, top, x, bottom)
        for y in range(top + step, bottom, step):
            painter.drawLine(left, y, right, y)

        painter.restore()
