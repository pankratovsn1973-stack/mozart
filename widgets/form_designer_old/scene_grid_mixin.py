# widgets/form_designer_old/scene_grid_mixin.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс-примесь GridMixin для графической сцены FormDesignerScene.
Обеспечивает гарантированную отрисовку координатной сетки ПОВЕРХ формы через drawForeground.
Решает проблему перекрытия сетки белой подложкой объекта self.background.
"""

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene


class GridMixin:
    """Миксин управления сеткой, накладываемой строго поверх геометрии формы."""

    def _init_grid(self):
        """Инициализация дефолтных параметров отображения сетки."""
        self._grid_visible = True
        self._snap_enabled = True
        self._grid_size = 10
        self._grid_color = QColor('#d0d0d0')  # Цвет линий сетки (серый)
        self._scene_bg_color = QColor('#e8e8e8')  # Фон вокруг формы
        self._form_bg_color = QColor('#ffffff')  # Фон самой формы (белый)

    def set_grid_visible(self, visible: bool):
        """Включает/выключает отображение сетки."""
        self._grid_visible = visible
        self._refresh_grid_layers()

    def set_snap_enabled(self, enabled: bool):
        """Метод вызывается из main_widget.py для управления привязкой."""
        self._snap_enabled = enabled

    def set_grid_size(self, size: int):
        """Метод вызывается из main_widget.py для изменения шага сетки."""
        self._grid_size = max(2, size)  # Защита от нулевого или отрицательного шага
        self._refresh_grid_layers()

    def _refresh_grid_layers(self):
        """Принудительно заставляет Qt перерисовать все слои сцены."""
        if hasattr(self, 'invalidate') and hasattr(self, 'sceneRect'):
            # Инвалидируем и фон, и передний план сцены
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
        # Полностью красим сцену в серый цвет «рабочей среды»
        painter.fillRect(rect, getattr(self, '_scene_bg_color', QColor('#e8e8e8')))

        # Если форма (background) существует, красим её подложку в белый цвет
        form_item = getattr(self, 'background', None)
        if form_item:
            painter.save()
            painter.setTransform(form_item.sceneTransform(), True)
            painter.fillRect(form_item.rect(), getattr(self, '_form_bg_color', QColor('#ffffff')))
            painter.restore()

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """
        Гарантированная отрисовка сетки в переднем слое (Foreground) строго по контуру формы.
        Исключает заглатывание линий белым фоном элементов и подложек.
        """
        super().drawForeground(painter, rect)

        # 1. Если сетка выключена кнопкой — ничего не чертим
        if not getattr(self, '_grid_visible', True):
            return

        # 2. Ищем форму на сцене
        form_item = getattr(self, 'background', None)
        if not form_item:
            return

        painter.save()

        # Привязываем координаты рисования к позиции формы на сцене
        painter.setTransform(form_item.sceneTransform(), True)
        f_rect = form_item.rect()

        # Настройка тонкого пера для сетки
        grid_pen = QPen(getattr(self, '_grid_color', QColor('#d0d0d0')), 1, Qt.SolidLine)
        painter.setPen(grid_pen)

        step = self._grid_size

        left = int(f_rect.left())
        top = int(f_rect.top())
        right = int(f_rect.right())
        bottom = int(f_rect.bottom())

        # Чертим вертикальные направляющие линии строго внутри границ формы
        for x in range(left + step, right, step):
            painter.drawLine(x, top, x, bottom)

        # Чертим горизонтальные направляющие линии строго внутри границ формы
        for y in range(top + step, bottom, step):
            painter.drawLine(left, y, right, y)

        painter.restore()
