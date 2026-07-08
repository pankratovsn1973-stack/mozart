# Полный путь: dialogs/__init__.py
"""
Экспорт диалогов и утилит для работы с классами.
"""
from .base_class_selector import BaseClassSelectorDialog
from .methods_dialog import MethodsDialog
from .signals_dialog import SignalsDialog
from .collection_manager import CollectionManager  # ДОБАВЛЕНО

__all__ = [
    'BaseClassSelectorDialog',
    'MethodsDialog',
    'SignalsDialog',
    'CollectionManager'  # ДОБАВЛЕНО
]