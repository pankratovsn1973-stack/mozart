# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_core/models.py
"""
Модели данных для Аналитика Моцарт.
Версия: 3.5 — добавлено поле t_full_text (полный текст файла/сущности)
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, JSON,
    ForeignKey, UUID, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ============================================================
# ТИПЫ СУЩНОСТЕЙ
# ============================================================
class EntityType:
    DIRECTORY = 1
    FILE = 2
    CLASS = 3
    PROCEDURE = 4
    METHOD = 5
    HEADER = 6
    LOCAL_VARIABLE = 7
    FUNCTION = 8
    IMPORT = 9
    PROPERTY = 10
    PARAMETER = 11
    GLOBAL_VARIABLE = 12
    CLASS_VARIABLE = 13

    @classmethod
    def get_name(cls, type_id: int) -> str:
        names = {
            cls.DIRECTORY: 'каталог',
            cls.FILE: 'файл',
            cls.CLASS: 'класс',
            cls.PROCEDURE: 'процедура',
            cls.METHOD: 'метод',
            cls.HEADER: 'заголовок',
            cls.LOCAL_VARIABLE: 'локальная переменная',
            cls.FUNCTION: 'функция',
            cls.IMPORT: 'импорт',
            cls.PROPERTY: 'свойство',
            cls.PARAMETER: 'параметр',
            cls.GLOBAL_VARIABLE: 'глобальная переменная',
            cls.CLASS_VARIABLE: 'переменная класса',
        }
        return names.get(type_id, f'неизвестный тип ({type_id})')

    @classmethod
    def get_icon(cls, type_id: int) -> str:
        icons = {
            cls.DIRECTORY: '📁',
            cls.FILE: '📄',
            cls.CLASS: '📦',
            cls.PROCEDURE: '⚡',
            cls.METHOD: '🔧',
            cls.HEADER: '📝',
            cls.LOCAL_VARIABLE: '🔤',
            cls.FUNCTION: '⚡',
            cls.IMPORT: '📥',
            cls.PROPERTY: '🔒',
            cls.PARAMETER: '📌',
            cls.GLOBAL_VARIABLE: '🌐',
            cls.CLASS_VARIABLE: '📋',
        }
        return icons.get(type_id, '❓')


# ============================================================
# ЕДИНАЯ ТАБЛИЦА СУЩНОСТЕЙ
# ============================================================
class Entity(Base):
    __tablename__ = 'tbl_entity'
    __table_args__ = (
        Index('idx_entity_type_id', 'type_id'),
        Index('idx_entity_parent_id', 'parent_id'),
        Index('idx_entity_dt_start', 'dt_start'),
        Index('idx_entity_dt_end', 'dt_end'),
        Index('idx_entity_name', 'c_name'),
        {'schema': 'mozart'}
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    type_id = Column(Integer, nullable=False)
    c_name = Column(String(500), nullable=False)
    parent_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=True)

    dt_start = Column(DateTime, default=datetime.now, nullable=False)
    dt_end = Column(DateTime, nullable=True)
    n_old_version = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=True)
    is_active = Column(Boolean, default=True)

    m_comment = Column(Text)
    n_order = Column(Integer, default=0)
    n_relise = Column(String(50))
    t_blobskript = Column(Text)

    # ============================================================
    # ПОЛНЫЙ ТЕКСТ ФАЙЛА/СУЩНОСТИ
    # ============================================================
    t_full_text = Column(Text, nullable=True)

    j_data = Column(JSON)

    # Явно указываем foreign_keys для устранения неоднозначности
    parent = relationship(
        'Entity',
        remote_side=[id],
        foreign_keys=[parent_id],
        backref='children'
    )

    old_version = relationship(
        'Entity',
        remote_side=[id],
        foreign_keys=[n_old_version],
        backref='newer_versions'
    )


# ============================================================
# ЗАДАЧИ
# ============================================================
class Task(Base):
    __tablename__ = 'tbl_task'
    __table_args__ = (
        Index('idx_task_number', 'task_number'),
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='draft')
    parent_task_id = Column(UUID, ForeignKey('mozart.tbl_task.id'), nullable=True)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    dt_start = Column(DateTime, default=datetime.now)
    dt_end = Column(DateTime, nullable=True)

    parent = relationship(
        'Task',
        remote_side=[id],
        foreign_keys=[parent_task_id],
        backref='children'
    )
    arch_solutions = relationship('ArchSolution', back_populates='task')
    candidates = relationship('TaskCandidate', back_populates='task')


class TaskCandidate(Base):
    __tablename__ = 'tbl_task_candidate'
    __table_args__ = (
        Index('idx_task_candidate_task', 'task_id'),
        Index('idx_task_candidate_target', 'target_id'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey('mozart.tbl_task.id'), nullable=False)
    target_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=False)
    impact_type = Column(String(20), nullable=False)
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    task = relationship('Task', back_populates='candidates')
    target = relationship('Entity', foreign_keys=[target_id])


# ============================================================
# АРХИТЕКТУРНЫЕ РЕШЕНИЯ
# ============================================================
class ArchSolution(Base):
    __tablename__ = 'tbl_arch_solution'
    __table_args__ = (
        Index('idx_arch_task', 'task_id'),
        Index('idx_arch_status', 'status'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey('mozart.tbl_task.id'), nullable=False)
    solution_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    approach = Column(String(50), default='monolith')
    tech_stack = Column(JSON)
    depends_on = Column(UUID, ForeignKey('mozart.tbl_arch_solution.id'), nullable=True)
    replaces = Column(UUID, ForeignKey('mozart.tbl_arch_solution.id'), nullable=True)
    status = Column(String(20), default='proposed')
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    dt_start = Column(DateTime, default=datetime.now)
    dt_end = Column(DateTime, nullable=True)

    task = relationship('Task', back_populates='arch_solutions')
    plans = relationship('Plan', back_populates='arch_solution')
    candidates = relationship('ArchCandidate', back_populates='arch_solution')


class ArchCandidate(Base):
    __tablename__ = 'tbl_arch_candidate'
    __table_args__ = (
        Index('idx_arch_candidate_arch', 'arch_solution_id'),
        Index('idx_arch_candidate_target', 'target_id'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    arch_solution_id = Column(UUID, ForeignKey('mozart.tbl_arch_solution.id'), nullable=False)
    target_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=False)
    impact_type = Column(String(20), nullable=False)
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    arch_solution = relationship('ArchSolution', back_populates='candidates')
    target = relationship('Entity', foreign_keys=[target_id])


# ============================================================
# ПЛАНЫ
# ============================================================
class Plan(Base):
    __tablename__ = 'tbl_plan'
    __table_args__ = (
        Index('idx_plan_arch', 'arch_solution_id'),
        Index('idx_plan_status', 'status'),
        Index('idx_plan_step', 'step_order'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    arch_solution_id = Column(UUID, ForeignKey('mozart.tbl_arch_solution.id'), nullable=False)
    plan_name = Column(String(255), nullable=False)
    description = Column(Text)
    step_order = Column(Integer, nullable=False)
    depends_on = Column(UUID, ForeignKey('mozart.tbl_plan.id'), nullable=True)
    assignee = Column(String(100))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    dt_start = Column(DateTime, default=datetime.now)
    dt_end = Column(DateTime, nullable=True)

    arch_solution = relationship('ArchSolution', back_populates='plans')
    actions = relationship('Action', back_populates='plan')
    candidates = relationship('PlanCandidate', back_populates='plan')


class PlanCandidate(Base):
    __tablename__ = 'tbl_plan_candidate'
    __table_args__ = (
        Index('idx_plan_candidate_plan', 'plan_id'),
        Index('idx_plan_candidate_target', 'target_id'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID, ForeignKey('mozart.tbl_plan.id'), nullable=False)
    target_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=False)
    impact_type = Column(String(20), nullable=False)
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    plan = relationship('Plan', back_populates='candidates')
    target = relationship('Entity', foreign_keys=[target_id])


# ============================================================
# ДЕЙСТВИЯ И РЕЗУЛЬТАТЫ
# ============================================================
class Action(Base):
    __tablename__ = 'tbl_action'
    __table_args__ = (
        Index('idx_action_plan', 'plan_id'),
        Index('idx_action_type', 'action_type'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID, ForeignKey('mozart.tbl_plan.id'), nullable=False)
    action_order = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    change_description = Column(Text, nullable=False)
    new_value = Column(JSON)
    precondition = Column(Text)
    postcondition = Column(Text)
    executed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    dt_start = Column(DateTime, default=datetime.now)
    dt_end = Column(DateTime, nullable=True)

    plan = relationship('Plan', back_populates='actions')
    result = relationship('ActionResult', back_populates='action', uselist=False)


class ActionResult(Base):
    __tablename__ = 'tbl_action_result'
    __table_args__ = (
        Index('idx_result_action', 'action_id'),
        Index('idx_result_target', 'target_id'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID, ForeignKey('mozart.tbl_action.id'), nullable=False)
    target_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=False)
    change_type = Column(String(20), nullable=False)
    old_snapshot = Column(JSON)
    new_snapshot = Column(JSON)
    new_version_id = Column(UUID)
    executed_at = Column(DateTime, default=datetime.now)

    action = relationship('Action', back_populates='result')
    target = relationship('Entity', foreign_keys=[target_id])


# ============================================================
# ГРАФ ВЫЗОВОВ
# ============================================================
class Call(Base):
    __tablename__ = 'tbl_call'
    __table_args__ = (
        Index('idx_call_callee', 'callee_name'),
        Index('idx_call_caller', 'caller_entity_id'),
        {'schema': 'mozart'}
    )
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    caller_entity_id = Column(UUID, ForeignKey('mozart.tbl_entity.id'), nullable=False)
    callee_name = Column(String(255), nullable=False)
    callee_type = Column(String(20), default='unknown')
    line_number = Column(Integer)
    is_active = Column(Boolean, default=True)
    dt_start = Column(DateTime, default=datetime.now)
    dt_end = Column(DateTime, nullable=True)

    caller_entity = relationship('Entity', foreign_keys=[caller_entity_id])