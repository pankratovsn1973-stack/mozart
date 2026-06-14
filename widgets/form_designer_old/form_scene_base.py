# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_scene_base.py

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal
from PySide6.QtGui import QBrush, QColor

class FormSceneBase(QGraphicsScene):
    """Базовый класс сцены, содержит общие атрибуты и сигналы."""

    control_selected = Signal(object)
    form_selected = Signal()
    form_resized = Signal(int, int)
    save_requested = Signal()
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.setSceneRect(0, 0, 3000, 2000)
        self.background = None          # будет установлен позже
        self.db = getattr(parent, 'db', None) if parent else None
        self.controls = {}              # {control_id: ControlItem}
        self.selected_control = None
        self.resize_handles = []
        self.control_handles = []