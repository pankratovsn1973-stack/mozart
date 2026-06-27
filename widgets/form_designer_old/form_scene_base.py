# widgets/form_designer_old/form_scene.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPen, QColor

from .form_background import FormBackground
from .resize_handle import ResizeHandle
from .scene_grid_mixin import GridMixin
from .scene_events_mixin import EventsMixin
from .scene_controls_mixin import ControlsMixin
from .form_objects_registry import FormObjectsRegistry


class FormDesignerScene(QGraphicsScene, GridMixin, EventsMixin, ControlsMixin):
    control_selected = Signal(object)
    form_resized = Signal(float, float)
    form_moved = Signal()
    form_geometry_changed = Signal()
    save_requested = Signal()
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

        if hasattr(self, '_init_context_metadata'):
            self._init_context_metadata()

    def set_db(self, db):
        self.db = db

    def init_form(self, width: float, height: float, title: str = "") -> FormBackground:
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

        self.background.form_geometry_changed.connect(self._on_form_geometry_changed)
        self.background.form_resized.connect(self._on_form_resized)

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
        if not view:
            return
        if view.horizontalScrollBar():
            view.horizontalScrollBar().setValue(0)
        if view.verticalScrollBar():
            view.verticalScrollBar().setValue(0)

    def _on_form_geometry_changed(self):
        self.form_geometry_changed.emit()

    def _on_form_resized(self, width, height):
        self.form_resized.emit(width, height)

    def select_control(self, widget_or_item):
        self.selected_control = widget_or_item if widget_or_item else self.background
        self.control_selected.emit(self.selected_control)

    def update_handles_position(self):
        if self.background and hasattr(self.background, 'update_handles_position'):
            self.background.update_handles_position()

    def drawItems(self, painter, numItems, items, options, widget=None):
        """Интеллектуальный перехват отрисовки: красим границы всей выделенной группы в синий пунктир."""
        # Отрисовываем базовые элементы сцены стандартно
        super().drawItems(painter, numItems, items, options, widget)

        # Настраиваем перо под фирменный синий пунктирный стиль ERP
        painter.save()
        pen = QPen(QColor('#0066ff'), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for item in items:
            # Если элемент выделен, не является бланком формы и не является маркером ресайза
            if item.isSelected() and item != self.background and not isinstance(item, ResizeHandle):
                # Прорисовываем синий пунктир строго по внешним физическим границам ControlItem
                painter.drawRect(item.sceneBoundingRect())

        painter.restore()
