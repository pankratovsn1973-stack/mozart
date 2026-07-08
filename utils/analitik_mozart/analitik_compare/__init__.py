# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_compare/__init__.py
"""
Пакет сравнения кода из БД и с диска.
Версия: 2.0 — для единой таблицы сущностей
"""

from analitik_compare.diff_engine import DiffEngine
from analitik_compare.diff_dialog import DiffDialog, show_diff_dialog

__all__ = [
    'DiffEngine',
    'DiffDialog',
    'show_diff_dialog'
]