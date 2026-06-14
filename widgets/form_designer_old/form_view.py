# /home/sergey/Documents/configurate/widgets/form_designer_old/form_view.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter


class FormDesignerView(QGraphicsView):
    """Вьювер для отображения сцены дизайнера форм"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRubberBandSelectionMode(Qt.ContainsItemShape)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setAcceptDrops(True)
        self._zoom = 1.0

    def wheelEvent(self, event):
        """Масштабирование колесиком мыши"""
        delta = event.angleDelta().y()
        if delta > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15
        self.scale(factor, factor)
        self._zoom *= factor

    def reset_zoom(self):
        """Сброс масштаба"""
        self.resetTransform()
        self._zoom = 1.0
