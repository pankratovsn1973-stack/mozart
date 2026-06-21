# widgets/form_designer_old/scene_grid_mixin.py
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene


class GridMixin:
    """Миксин управления сеткой — теперь только логика, без рисования!"""

    def _init_grid(self):
        """Инициализация параметров сетки."""
        self._grid_visible = True
        self._snap_enabled = True
        self._grid_size = 10
        self._scene_bg_color = QColor('#e8e8e8')

    def set_grid_visible(self, visible: bool):
        """Включает/выключает сетку (прокси на форму)."""
        self._grid_visible = visible
        # Перенаправляем на форму
        if hasattr(self, 'background') and self.background:
            if hasattr(self.background, 'set_show_grid'):
                self.background.set_show_grid(visible)
        self._refresh_view()

    def set_grid_size(self, size: int):
        """Меняет размер сетки (прокси на форму)."""
        self._grid_size = max(2, size)
        if hasattr(self, 'background') and self.background:
            if hasattr(self.background, 'set_grid_size'):
                self.background.set_grid_size(size)
        self._refresh_view()

    def set_snap_enabled(self, enabled: bool):
        """Включает/выключает привязку к сетке."""
        self._snap_enabled = enabled

    def snap_to_grid(self, pos: QPointF) -> QPointF:
        """Округляет координаты до ближайшего шага сетки."""
        if not getattr(self, '_snap_enabled', True) or self._grid_size <= 1:
            return pos
        x = round(pos.x() / self._grid_size) * self._grid_size
        y = round(pos.y() / self._grid_size) * self._grid_size
        return QPointF(max(0.0, x), max(0.0, y))

    def _refresh_view(self):
        """Принудительно обновляет отображение."""
        self.update()
        for view in self.views():
            if view and view.viewport():
                view.viewport().update()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Рисует только фон сцены (серый). Сетку НЕ рисуем!"""
        painter.fillRect(rect, getattr(self, '_scene_bg_color', QColor('#e8e8e8')))

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """Здесь НЕ рисуем сетку — она рисуется в FormBackground.paint()!"""
        # Просто вызываем базовый метод (он пустой)
        super().drawForeground(painter, rect)