# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_scene.py

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPen, QColor

from .form_background import FormBackground
from .resize_handle import ResizeHandle
from .scene_grid_mixin import GridMixin
from .scene_events_mixin import EventsMixin
from .scene_controls_mixin import ControlsMixin
from .scene_loader_mixin import SceneLoaderMixin
from .form_objects_registry import FormObjectsRegistry


class FormDesignerScene(QGraphicsScene, GridMixin, EventsMixin, ControlsMixin, SceneLoaderMixin):
    """Графическая сцена визуального проектирования форм Mozart ERP."""
    control_selected = Signal(object)
    form_resized = Signal(float, float)
    form_geometry_changed = Signal()
    control_added = Signal(object)
    control_deleted = Signal(str)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = None
        self.controls = {}
        self.selected_control = None
        self.db = None

        self.setSceneRect(0, 0, 3000, 2000)
        self._init_grid()
        self._init_controls()

        if hasattr(self, '_init_context_metadata'):
            self._init_context_metadata()

    def set_db(self, db):
        self.db = db

    def init_form(self, width: float, height: float, title: str = "") -> FormBackground:
        """Атомарная инициализация визуального бланка формы."""
        FormObjectsRegistry().clear_registry()

        if self.background:
            for handle in getattr(self.background, '_handles', []):
                if handle and handle.scene() == self:
                    self.removeItem(handle)
            if self.background.scene() == self:
                self.removeItem(self.background)
            self.background = None

        self.background = FormBackground(width, height, title)
        self.background.setPos(0, 0)
        self.addItem(self.background)

        self.background.form_geometry_changed.connect(lambda: self.form_geometry_changed.emit())
        self.background.form_resized.connect(lambda w, h: self.form_resized.emit(w, h))

        handle = ResizeHandle(4, self.background, parent=self.background)
        self.background._handles = [handle]
        self.background.update_handles_position()

        self.setSceneRect(0, 0, 3000, 2000)
        self.update()

        for view in self.views():
            view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            view.centerOn(0.0, 0.0)
            QTimer.singleShot(0, lambda v=view: self._reset_view_scrollbars(v))

        return self.background

    def _reset_view_scrollbars(self, view):
        if view and view.horizontalScrollBar():
            view.horizontalScrollBar().setValue(0)
        if view and view.verticalScrollBar():
            view.verticalScrollBar().setValue(0)

    def drawItems(self, painter, numItems, items, options, widget=None):
        """Интеллектуальная отрисовка синей пунктирной рамки вокруг выделенных элементов."""
        super().drawItems(painter, numItems, items, options, widget)

        painter.save()
        pen = QPen(QColor('#0066ff'), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for item in items:
            if item.isSelected() and item != self.background and not isinstance(item, ResizeHandle):
                painter.drawRect(item.sceneBoundingRect())

        painter.restore()
