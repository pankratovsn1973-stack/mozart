# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item_base.py

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsItem


class ControlItemBase(QGraphicsProxyWidget):
    """Базовый C++ графический контейнер PySide6 для проксирования виджетов на сцене."""

    def __init__(self, widget, control_id, control_type, parent=None):
        super().__init__(parent)
        self.control_type = str(control_type).lower()

        if widget:
            self.setWidget(widget)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        """Перехват C++ изменений состояний графического элемента на сцене."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value

            if hasattr(self, 'update_handles_position'):
                try:
                    self.update_handles_position()
                except:
                    pass

            if hasattr(self, 'geometry_changed') and hasattr(self, 'control_id'):
                rect = self.rect()
                self.geometry_changed.emit(self.control_id, int(new_pos.x()), int(new_pos.y()), int(rect.width()),
                                           int(rect.height()))

        return super().itemChange(change, value)
