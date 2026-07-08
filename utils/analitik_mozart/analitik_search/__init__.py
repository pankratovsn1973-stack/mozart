# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_search/__init__.py
"""
Глобальный поиск по коду для Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
"""

from analitik_search.search import CodeSearch, SearchDialog, show_search_dialog

__all__ = [
    'CodeSearch',
    'SearchDialog',
    'show_search_dialog'
]