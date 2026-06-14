# tabs/entity_subtabs/__init__.py
from .fields_tab import FieldsTab
from .bu_visibility_tab import BUVISibilityTab
from .composition_tab import CompositionTab
from .routes_tab import RoutesTab
from .import_tab import ImportTab   # раскомментируем

__all__ = [
    'FieldsTab',
    'BUVISibilityTab',
    'CompositionTab',
    'RoutesTab',
    'ImportTab'
]