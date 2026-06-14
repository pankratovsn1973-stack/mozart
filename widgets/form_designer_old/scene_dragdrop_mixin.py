# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_dragdrop_mixin.py

import uuid
from PySide6.QtCore import QPointF

class DragDropMixin:
    """Миксин: перетаскивание контролов из палитры."""

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.background:
            event.ignore()
            return

        control_type = event.mimeData().text()
        if not control_type:
            event.ignore()
            return

        scene_pos = event.scenePosition()
        if self.snap_enabled:
            scene_pos = self.snap_point(scene_pos)

        form_pos = self.background.mapFromScene(scene_pos)
        x = form_pos.x()
        y = form_pos.y()

        # Ограничения
        w_default = 150
        h_default = 30
        max_x = self.background.width - w_default
        max_y = self.background.height - 30
        x = max(0, min(x, max_x))
        y = max(30, min(y, max_y))

        from controls import create_control
        widget = create_control(control_type, parent=None, db=self.db)
        if widget:
            control_id = str(uuid.uuid4())[:8]
            widget.setObjectName(f"{control_type}_{control_id}")
            self.add_control(widget, control_id, control_type, x, y)
            self.clear_selection()
            self.controls[control_id].set_selected(True)
            event.acceptProposedAction()
        else:
            event.ignore()