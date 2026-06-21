# widgets/form_designer_old/__init__.py
# -*- coding: utf-8 -*-

from .main_widget import FormDesigner
from .form_scene import FormDesignerScene
from .form_background import FormBackground
from .control_item import ControlItem
from .resize_handle import ResizeHandle
from .property_editor import PropertyEditor
from .palette_widget import PaletteWidget
# ИСПРАВЛЕНИЕ: Импортируем только ToolBarBar, так как ToolBarButton больше не нужен
from .toolbar_bar import ToolBarBar

__all__ = [
    'FormDesigner',
    'FormDesignerScene',
    'FormBackground',
    'ControlItem',
    'ResizeHandle',
    'PropertyEditor',
    'PaletteWidget',
    'ToolBarBar'
]
