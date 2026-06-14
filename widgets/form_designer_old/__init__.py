# widgets/form_designer_old/__init__.py
# -*- coding: utf-8 -*-

from .main_widget import FormDesigner
from .form_scene import FormDesignerScene
from .form_view import FormDesignerView
from .control_item import ControlItem
from .palette_widget import PaletteWidget
from .property_panel import PropertyPanel
from .methods_panel import MethodsPanel
from .events_panel import EventsPanel
from .code_editor import CodeEditorDialog
from .grid_manager import GridManager
from .resize_handle import ResizeHandle
from .title_bar import TitleBar
from .toolbar_bar import ToolBarBar, ToolBarButton
from .statusbar_bar import StatusBarBar
from .form_background import FormBackground
from .property_inspector import PropertyInspector
# И добавьте 'PropertyInspector' в массив __all__
__all__ = [
    'FormDesigner',
    'FormDesignerScene',
    'FormDesignerView',
    'ControlItem',
    'PaletteWidget',
    'PropertyPanel',
    'MethodsPanel',
    'EventsPanel',
    'CodeEditorDialog',
    'GridManager',
    'ResizeHandle',
    'TitleBar',
    'ToolBarBar',
    'ToolBarButton',
    'StatusBarBar',
    'PropertyInspector',
    'FormBackground'
]
