# mozart_import/graph/graphics_view.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QWheelEvent

from .link_line import LinkLine


class GraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)

        # Исправлено: используем QGraphicsView.ScrollHandDrag
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFocusPolicy(Qt.StrongFocus)
        self.scale_factor = 1.0

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_view(1.25)
            elif delta < 0:
                self.scale_view(0.8)
        else:
            super().wheelEvent(event)

    def scale_view(self, factor):
        self.scale_factor *= factor
        self.scale(factor, factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            scene = self.scene()
            for item in scene.selectedItems():
                if isinstance(item, LinkLine):
                    if hasattr(scene, 'remove_link'):
                        scene.remove_link(item)
            event.accept()
        else:
            super().keyPressEvent(event)