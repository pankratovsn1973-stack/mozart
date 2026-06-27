# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/designer_panels.py

from PySide6.QtWidgets import QSplitter, QSizePolicy
from PySide6.QtCore import Qt

from .palette_widget import PaletteWidget
from .hierarchy_widget import HierarchyWidget
from .property_editor import PropertyEditor


class DesignerPanels:
    """Управление боковыми панелями дизайнера с корректными импортами PySide6."""

    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

        # Левый сплиттер (палитра + иерархия)
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.palette = PaletteWidget(parent)
        self.hierarchy = HierarchyWidget(parent)
        self.left_splitter.addWidget(self.palette)
        self.left_splitter.addWidget(self.hierarchy)
        self.left_splitter.setSizes([300, 200])

        # Правый сплиттер (свойства)
        self.right_panel = PropertyEditor(parent)
        self.right_panel.setMinimumWidth(10)
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

        # Подключение сигналов
        self.hierarchy.item_selected.connect(self._on_hierarchy_selected)
        self.right_panel.property_changed.connect(self._on_property_changed)

    def _on_hierarchy_selected(self, control_id):
        if hasattr(self.parent.scene, 'select_control_by_id'):
            self.parent.scene.select_control_by_id(control_id)

    def _on_property_changed(self, prop_name, value):
        if hasattr(self.parent, 'on_property_changed'):
            self.parent.on_property_changed(prop_name, value)

    def get_palette(self):
        return self.palette

    def get_hierarchy(self):
        return self.hierarchy

    def get_right_panel(self):
        return self.right_panel

    def retranslate(self, tr):
        self.hierarchy.retranslate_ui()

    def update_for_control(self, control_item):
        if control_item:
            self.right_panel.set_control(control_item)
            if hasattr(self.hierarchy, 'select_item_by_id'):
                self.hierarchy.select_item_by_id(control_item.control_id)
        else:
            self.right_panel.set_form(self.parent)
            if hasattr(self.hierarchy, 'clear_selection'):
                self.hierarchy.clear_selection()
