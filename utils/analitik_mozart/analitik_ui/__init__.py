# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/__init__.py

from .tree_tasks import TreeTasks
from .ai_assistant_dialog import AIAssistantDialog, show_ai_assistant
from .collect_dialog import show_collect_dialog, show_collect_directory_dialog
from .usage_dialog import show_usage_dialog
from .assemble_dialog import AssemblePreviewDialog  # <-- ДОБАВИТЬ

__all__ = [
    'TreeTasks',
    'AIAssistantDialog',
    'show_ai_assistant',
    'show_collect_dialog',
    'show_collect_directory_dialog',
    'show_usage_dialog',
    'AssemblePreviewDialog'  # <-- ДОБАВИТЬ
]