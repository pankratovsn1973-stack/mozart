# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_scene.py

from PySide6.QtWidgets import QGraphicsScene
from .form_scene_base import FormSceneBase
from .scene_grid_mixin import GridMixin
from .scene_dragdrop_mixin import DragDropMixin
from .scene_controls_mixin import ControlsMixin
from .scene_events_mixin import EventsMixin

class FormDesignerScene(GridMixin, DragDropMixin, ControlsMixin, EventsMixin, FormSceneBase):
    """Полноценная сцена для визуального дизайнера форм."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_grid()
        self._init_controls()
        self.resize_handles = []
        self.control_handles = []

    def init_form(self, width=800, height=600, title="Форма"):
        """Создаёт бланк формы и размещает на сцене."""
        from .form_background import FormBackground
        from .resize_handle import ResizeHandle

        for handle in self.resize_handles:
            if handle.scene():
                self.removeItem(handle)
        self.resize_handles.clear()
        self.clear_selection()

        if self.background:
            if self.background.title_bar and self.background.title_bar.scene():
                self.removeItem(self.background.title_bar)
            if self.background.tool_bar and self.background.tool_bar.scene():
                self.removeItem(self.background.tool_bar)
            if self.background.status_bar and self.background.status_bar.scene():
                self.removeItem(self.background.status_bar)
            self.removeItem(self.background)

        self.background = FormBackground(width, height, title)
        title_bar_height = self.background.title_bar.get_height() if self.background.title_bar else 32
        self.background.setPos(0, title_bar_height)
        self.addItem(self.background)

        for pos_key in ResizeHandle.POSITIONS.keys():
            handle = ResizeHandle(pos_key, self.background)
            self.resize_handles.append(handle)
            handle.update_position()

        self.form_resized.emit(width, height)
        return self.background