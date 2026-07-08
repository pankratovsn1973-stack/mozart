# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ai/__init__.py
"""
ИИ-модуль Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
"""

from analitik_ai.context_builder import ContextBuilder

# Агенты пока не реализованы — оставляем заглушки для обратной совместимости
try:
    from analitik_ai.agents import (
        BaseAgent,
        ArchitectAgent,
        PlannerAgent,
        CoderAgent,
        RefactorAgent,
        TesterAgent
    )
except ImportError:
    # Создаём заглушки
    class BaseAgent:
        pass


    class ArchitectAgent(BaseAgent):
        pass


    class PlannerAgent(BaseAgent):
        pass


    class CoderAgent(BaseAgent):
        pass


    class RefactorAgent(BaseAgent):
        pass


    class TesterAgent(BaseAgent):
        pass

try:
    from analitik_ai.orchestrator import AIOrchestrator
except ImportError:
    class AIOrchestrator:
        pass

__all__ = [
    'ContextBuilder',
    'BaseAgent',
    'ArchitectAgent',
    'PlannerAgent',
    'CoderAgent',
    'RefactorAgent',
    'TesterAgent',
    'AIOrchestrator'
]