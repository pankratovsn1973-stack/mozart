# widgets/form_designer_old/form_scene.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс FormDesignerScene (наследник QGraphicsScene).
Управляет графическим холстом визуального редактора форм Mozart ERP.
Исправлен баг отсутствия свойства selected_control в конструкторе сцены.
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, QRectF, Signal

from .form_background import FormBackground
from .resize_handle import ResizeHandle
from .scene_grid_mixin import GridMixin
from .scene_events_mixin import EventsMixin
from .scene_controls_mixin import ControlsMixin


class FormDesignerScene(QGraphicsScene, GridMixin, EventsMixin, ControlsMixin):
    """Главная графическая сцена визуального редактора форм."""

    control_selected = Signal(object)
    form_resized = Signal(float, float)
    save_requested = Signal()
    control_added = Signal(object)
    control_deleted = Signal(str)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = None
        self.controls = {}

        # ИСПРАВЛЕНО: Добавлено свойство трекинга выделенного объекта для main_widget.py (строка 173)
        self.selected_control = None

        self._init_grid()

    def init_form(self, width: float, height: float, title: str) -> FormBackground:
        """Инициализация холста проектируемой формы и создание 8 волшебных точек."""
        if self.background:
            if hasattr(self.background, 'title_bar'): self.removeItem(self.background.title_bar)
            if hasattr(self.background, 'tool_bar'): self.removeItem(self.background.tool_bar)
            if hasattr(self.background, 'status_bar'): self.removeItem(self.background.status_bar)
            for handle in getattr(self.background, '_handles', []):
                self.removeItem(handle)
            self.removeItem(self.background)

        self.background = FormBackground(width, height, title)
        self.addItem(self.background)

        if self.background.title_bar: self.addItem(self.background.title_bar)
        if self.background.tool_bar: self.addItem(self.background.tool_bar)
        if self.background.status_bar: self.addItem(self.background.status_bar)

        self.background._handles = []
        for pos_key in ResizeHandle.POSITIONS.keys():
            handle = ResizeHandle(pos_key, self.background)
            self.addItem(handle)
            self.background._handles.append(handle)

        self.setSceneRect(self.itemsBoundingRect())
        self.update()
        return self.background

    def select_control(self, widget_or_item):
        """
        Метод оповещения сцены о выборе конкретного контрола.
        Синхронизирует внутреннее свойство selected_control и выстреливает сигнал.
        """
        # ИСПРАВЛЕНО: Сохраняем ссылку на выделенный графический элемент или форму
        self.selected_control = widget_or_item if widget_or_item else self.background
        self.control_selected.emit(self.selected_control)
