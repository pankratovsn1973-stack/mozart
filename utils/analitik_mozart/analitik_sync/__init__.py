# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_sync/__init__.py
"""
Подсистема автоматической синхронизации Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
"""

from analitik_sync.watcher import SyncManager, CodeChangeHandler, sync_project

__all__ = [
    'SyncManager',
    'CodeChangeHandler',
    'sync_project'
]