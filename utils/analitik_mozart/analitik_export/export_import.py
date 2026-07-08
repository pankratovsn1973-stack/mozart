# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_export/export_import.py
"""
Экспорт и импорт данных Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
Полная версия со всеми типами сущностей
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import text

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressDialog, QMessageBox,
    QCheckBox, QGroupBox, QComboBox, QFormLayout,
    QSpinBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt

from analitik_core.database import get_session, get_db
from analitik_core.models import (
    Entity, Task, ArchSolution, Plan, Action, ActionResult, Call,
    EntityType
)


class ExportImportManager:
    """Управление экспортом и импортом данных."""

    def __init__(self, db_session=None):
        self.db_session = db_session or get_session()
        self.db = get_db()

    # ================================================================
    # ЭКСПОРТ
    # ================================================================

    def export_all(self, file_path: str, include_history: bool = True,
                   export_tasks: bool = True, export_calls: bool = True) -> Dict:
        """
        Экспортирует все данные в JSON.
        """
        data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'schema': 'mozart',
                'total_records': 0,
                'include_history': include_history
            },
            'entities': [],
            'tasks': [],
            'arch_solutions': [],
            'plans': [],
            'actions': [],
            'action_results': [],
            'calls': [],
            'task_candidates': [],
            'arch_candidates': [],
            'plan_candidates': []
        }

        # 1. Экспортируем сущности
        query = self.db_session.query(Entity)
        if not include_history:
            query = query.filter(Entity.is_active == True)

        for entity in query.all():
            data['entities'].append(self._entity_to_dict(entity))

        # 2. Экспортируем задачи
        if export_tasks:
            query = self.db_session.query(Task)
            if not include_history:
                query = query.filter(Task.is_active == True)

            for task in query.all():
                data['tasks'].append(self._task_to_dict(task))

            # 2.1 Кандидаты задач
            from analitik_core.models import TaskCandidate
            query = self.db_session.query(TaskCandidate)
            if not include_history:
                query = query.filter(TaskCandidate.is_active == True)

            for candidate in query.all():
                data['task_candidates'].append(self._task_candidate_to_dict(candidate))

            # 3. Архитектурные решения
            query = self.db_session.query(ArchSolution)
            if not include_history:
                query = query.filter(ArchSolution.is_active == True)

            for arch in query.all():
                data['arch_solutions'].append(self._arch_to_dict(arch))

            # 3.1 Кандидаты архитектуры
            from analitik_core.models import ArchCandidate
            query = self.db_session.query(ArchCandidate)
            if not include_history:
                query = query.filter(ArchCandidate.is_active == True)

            for candidate in query.all():
                data['arch_candidates'].append(self._arch_candidate_to_dict(candidate))

            # 4. Планы
            query = self.db_session.query(Plan)
            if not include_history:
                query = query.filter(Plan.is_active == True)

            for plan in query.all():
                data['plans'].append(self._plan_to_dict(plan))

            # 4.1 Кандидаты планов
            from analitik_core.models import PlanCandidate
            query = self.db_session.query(PlanCandidate)
            if not include_history:
                query = query.filter(PlanCandidate.is_active == True)

            for candidate in query.all():
                data['plan_candidates'].append(self._plan_candidate_to_dict(candidate))

            # 5. Действия
            query = self.db_session.query(Action)
            if not include_history:
                query = query.filter(Action.is_active == True)

            for action in query.all():
                data['actions'].append(self._action_to_dict(action))

            # 6. Результаты действий
            query = self.db_session.query(ActionResult)
            if not include_history:
                query = query.filter(ActionResult.is_active == True)

            for result in query.all():
                data['action_results'].append(self._result_to_dict(result))

        # 7. Вызовы
        if export_calls:
            query = self.db_session.query(Call)
            if not include_history:
                query = query.filter(Call.is_active == True)

            for call in query.all():
                data['calls'].append(self._call_to_dict(call))

        # Подсчитываем общее количество
        total = 0
        for key, value in data.items():
            if isinstance(value, list):
                total += len(value)

        data['export_info']['total_records'] = total

        # Сохраняем в файл
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return data

    def export_entities_by_type(self, file_path: str, type_id: int,
                                include_history: bool = True) -> Dict:
        """
        Экспортирует сущности определённого типа.
        """
        query = self.db_session.query(Entity).filter(Entity.type_id == type_id)
        if not include_history:
            query = query.filter(Entity.is_active == True)

        data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'type_id': type_id,
                'type_name': EntityType.get_name(type_id),
                'total_records': 0
            },
            'entities': []
        }

        for entity in query.all():
            data['entities'].append(self._entity_to_dict(entity))

        data['export_info']['total_records'] = len(data['entities'])

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return data

    def export_task_with_entities(self, file_path: str, task_id: str) -> Dict:
        """
        Экспортирует задачу со всеми связанными сущностями.
        """
        task = self.db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {'error': 'Задача не найдена'}

        data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'task_id': task_id,
                'task_number': task.task_number
            },
            'task': self._task_to_dict(task),
            'entities': [],
            'task_candidates': [],
            'arch_solutions': [],
            'arch_candidates': [],
            'plans': [],
            'plan_candidates': [],
            'actions': [],
            'action_results': []
        }

        # Кандидаты задачи
        from analitik_core.models import TaskCandidate
        candidates = self.db_session.query(TaskCandidate).filter(
            TaskCandidate.task_id == task_id,
            TaskCandidate.is_active == True
        ).all()

        entity_ids = set()
        for candidate in candidates:
            data['task_candidates'].append(self._task_candidate_to_dict(candidate))
            entity_ids.add(candidate.target_id)

        # Сущности
        for entity_id in entity_ids:
            entity = self.db_session.query(Entity).filter(Entity.id == entity_id).first()
            if entity:
                data['entities'].append(self._entity_to_dict(entity))

        # Архитектурные решения
        archs = self.db_session.query(ArchSolution).filter(
            ArchSolution.task_id == task_id,
            ArchSolution.is_active == True
        ).all()

        for arch in archs:
            data['arch_solutions'].append(self._arch_to_dict(arch))

            # Кандидаты архитектуры
            arch_candidates = self.db_session.query(ArchCandidate).filter(
                ArchCandidate.arch_solution_id == arch.id,
                ArchCandidate.is_active == True
            ).all()

            for candidate in arch_candidates:
                data['arch_candidates'].append(self._arch_candidate_to_dict(candidate))

            # Планы
            plans = self.db_session.query(Plan).filter(
                Plan.arch_solution_id == arch.id,
                Plan.is_active == True
            ).all()

            for plan in plans:
                data['plans'].append(self._plan_to_dict(plan))

                # Кандидаты планов
                plan_candidates = self.db_session.query(PlanCandidate).filter(
                    PlanCandidate.plan_id == plan.id,
                    PlanCandidate.is_active == True
                ).all()

                for candidate in plan_candidates:
                    data['plan_candidates'].append(self._plan_candidate_to_dict(candidate))

                # Действия
                actions = self.db_session.query(Action).filter(
                    Action.plan_id == plan.id,
                    Action.is_active == True
                ).all()

                for action in actions:
                    data['actions'].append(self._action_to_dict(action))

                    # Результаты
                    result = self.db_session.query(ActionResult).filter(
                        ActionResult.action_id == action.id,
                        ActionResult.is_active == True
                    ).first()

                    if result:
                        data['action_results'].append(self._result_to_dict(result))

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return data

    # ================================================================
    # КОНВЕРТАЦИЯ В СЛОВАРИ
    # ================================================================

    def _entity_to_dict(self, entity: Entity) -> Dict:
        """Конвертирует сущность в словарь."""
        return {
            'id': str(entity.id),
            'type_id': entity.type_id,
            'type_name': EntityType.get_name(entity.type_id),
            'c_name': entity.c_name,
            'parent_id': str(entity.parent_id) if entity.parent_id else None,
            'dt_start': entity.dt_start.isoformat() if entity.dt_start else None,
            'dt_end': entity.dt_end.isoformat() if entity.dt_end else None,
            'n_old_version': str(entity.n_old_version) if entity.n_old_version else None,
            'is_active': entity.is_active,
            'm_comment': entity.m_comment,
            'n_order': entity.n_order,
            'n_relise': entity.n_relise,
            't_blobskript': entity.t_blobskript,
            'j_data': entity.j_data
        }

    def _task_to_dict(self, task: Task) -> Dict:
        return {
            'id': str(task.id),
            'task_number': task.task_number,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'parent_task_id': str(task.parent_task_id) if task.parent_task_id else None,
            'created_by': task.created_by,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'is_active': task.is_active,
            'dt_start': task.dt_start.isoformat() if task.dt_start else None,
            'dt_end': task.dt_end.isoformat() if task.dt_end else None
        }

    def _task_candidate_to_dict(self, candidate) -> Dict:
        return {
            'id': str(candidate.id),
            'task_id': str(candidate.task_id),
            'target_id': str(candidate.target_id),
            'impact_type': candidate.impact_type,
            'justification': candidate.justification,
            'created_at': candidate.created_at.isoformat() if candidate.created_at else None
        }

    def _arch_to_dict(self, arch: ArchSolution) -> Dict:
        return {
            'id': str(arch.id),
            'task_id': str(arch.task_id),
            'solution_name': arch.solution_name,
            'description': arch.description,
            'approach': arch.approach,
            'tech_stack': arch.tech_stack,
            'depends_on': str(arch.depends_on) if arch.depends_on else None,
            'replaces': str(arch.replaces) if arch.replaces else None,
            'status': arch.status,
            'created_by': arch.created_by,
            'created_at': arch.created_at.isoformat() if arch.created_at else None,
            'is_active': arch.is_active,
            'dt_start': arch.dt_start.isoformat() if arch.dt_start else None,
            'dt_end': arch.dt_end.isoformat() if arch.dt_end else None
        }

    def _arch_candidate_to_dict(self, candidate) -> Dict:
        return {
            'id': str(candidate.id),
            'arch_solution_id': str(candidate.arch_solution_id),
            'target_id': str(candidate.target_id),
            'impact_type': candidate.impact_type,
            'justification': candidate.justification,
            'created_at': candidate.created_at.isoformat() if candidate.created_at else None
        }

    def _plan_to_dict(self, plan: Plan) -> Dict:
        return {
            'id': str(plan.id),
            'arch_solution_id': str(plan.arch_solution_id),
            'plan_name': plan.plan_name,
            'description': plan.description,
            'step_order': plan.step_order,
            'depends_on': str(plan.depends_on) if plan.depends_on else None,
            'assignee': plan.assignee,
            'status': plan.status,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'completed_at': plan.completed_at.isoformat() if plan.completed_at else None,
            'is_active': plan.is_active,
            'dt_start': plan.dt_start.isoformat() if plan.dt_start else None,
            'dt_end': plan.dt_end.isoformat() if plan.dt_end else None
        }

    def _plan_candidate_to_dict(self, candidate) -> Dict:
        return {
            'id': str(candidate.id),
            'plan_id': str(candidate.plan_id),
            'target_id': str(candidate.target_id),
            'impact_type': candidate.impact_type,
            'justification': candidate.justification,
            'created_at': candidate.created_at.isoformat() if candidate.created_at else None
        }

    def _action_to_dict(self, action: Action) -> Dict:
        return {
            'id': str(action.id),
            'plan_id': str(action.plan_id),
            'action_order': action.action_order,
            'action_type': action.action_type,
            'change_description': action.change_description,
            'new_value': action.new_value,
            'precondition': action.precondition,
            'postcondition': action.postcondition,
            'executed_at': action.executed_at.isoformat() if action.executed_at else None,
            'is_active': action.is_active,
            'dt_start': action.dt_start.isoformat() if action.dt_start else None,
            'dt_end': action.dt_end.isoformat() if action.dt_end else None
        }

    def _result_to_dict(self, result: ActionResult) -> Dict:
        return {
            'id': str(result.id),
            'action_id': str(result.action_id),
            'target_id': str(result.target_id),
            'change_type': result.change_type,
            'old_snapshot': result.old_snapshot,
            'new_snapshot': result.new_snapshot,
            'new_version_id': str(result.new_version_id) if result.new_version_id else None,
            'executed_at': result.executed_at.isoformat() if result.executed_at else None
        }

    def _call_to_dict(self, call: Call) -> Dict:
        return {
            'id': str(call.id),
            'caller_entity_id': str(call.caller_entity_id),
            'callee_name': call.callee_name,
            'callee_type': call.callee_type,
            'line_number': call.line_number,
            'is_active': call.is_active,
            'dt_start': call.dt_start.isoformat() if call.dt_start else None,
            'dt_end': call.dt_end.isoformat() if call.dt_end else None
        }

    # ================================================================
    # ИМПОРТ
    # ================================================================

    def import_data(self, file_path: str, clear_existing: bool = False,
                    import_mode: str = 'all') -> Dict:
        """
        Импортирует данные из JSON.

        Args:
            file_path: Путь к файлу
            clear_existing: Очистить существующие данные
            import_mode: 'all', 'entities', 'tasks', 'calls'
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stats = {
            'entities': 0,
            'tasks': 0,
            'task_candidates': 0,
            'arch_solutions': 0,
            'arch_candidates': 0,
            'plans': 0,
            'plan_candidates': 0,
            'actions': 0,
            'action_results': 0,
            'calls': 0
        }

        if clear_existing:
            self._clear_all()

        # Импортируем в порядке зависимостей
        if import_mode in ('all', 'entities'):
            stats['entities'] = self._import_entities(data.get('entities', []))

        if import_mode in ('all', 'tasks'):
            stats['tasks'] = self._import_tasks(data.get('tasks', []))
            stats['task_candidates'] = self._import_task_candidates(data.get('task_candidates', []))
            stats['arch_solutions'] = self._import_arch_solutions(data.get('arch_solutions', []))
            stats['arch_candidates'] = self._import_arch_candidates(data.get('arch_candidates', []))
            stats['plans'] = self._import_plans(data.get('plans', []))
            stats['plan_candidates'] = self._import_plan_candidates(data.get('plan_candidates', []))
            stats['actions'] = self._import_actions(data.get('actions', []))
            stats['action_results'] = self._import_action_results(data.get('action_results', []))

        if import_mode in ('all', 'calls'):
            stats['calls'] = self._import_calls(data.get('calls', []))

        self.db_session.commit()
        return stats

    def _clear_all(self):
        """Очищает все таблицы."""
        tables = [
            ActionResult, Action, Plan, ArchSolution, Task,
            Call, Entity
        ]
        # Очищаем в правильном порядке (сначала дочерние)
        for table in reversed(tables):
            try:
                self.db_session.query(table).delete()
            except Exception:
                pass
        self.db_session.commit()

    def _import_entities(self, data: List[Dict]) -> int:
        """Импортирует сущности."""
        count = 0
        for item in data:
            # Проверяем, не существует ли уже
            existing = self.db_session.query(Entity).filter(
                Entity.id == item.get('id')
            ).first()

            if existing:
                continue

            entity = Entity(
                id=item.get('id'),
                type_id=item['type_id'],
                c_name=item['c_name'],
                parent_id=item.get('parent_id'),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None,
                n_old_version=item.get('n_old_version'),
                is_active=item.get('is_active', True),
                m_comment=item.get('m_comment'),
                n_order=item.get('n_order', 0),
                n_relise=item.get('n_relise'),
                t_blobskript=item.get('t_blobskript'),
                j_data=item.get('j_data')
            )
            self.db_session.add(entity)
            count += 1
        return count

    def _import_tasks(self, data: List[Dict]) -> int:
        """Импортирует задачи."""
        count = 0
        for item in data:
            existing = self.db_session.query(Task).filter(
                Task.id == item.get('id')
            ).first()

            if existing:
                continue

            task = Task(
                id=item.get('id'),
                task_number=item['task_number'],
                title=item['title'],
                description=item['description'],
                priority=item.get('priority', 'medium'),
                status=item.get('status', 'draft'),
                parent_task_id=item.get('parent_task_id'),
                created_by=item.get('created_by'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now(),
                deadline=datetime.fromisoformat(item['deadline']) if item.get('deadline') else None,
                is_active=item.get('is_active', True),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None
            )
            self.db_session.add(task)
            count += 1
        return count

    def _import_task_candidates(self, data: List[Dict]) -> int:
        """Импортирует кандидатов задач."""
        from analitik_core.models import TaskCandidate
        count = 0
        for item in data:
            existing = self.db_session.query(TaskCandidate).filter(
                TaskCandidate.id == item.get('id')
            ).first()

            if existing:
                continue

            candidate = TaskCandidate(
                id=item.get('id'),
                task_id=item['task_id'],
                target_id=item['target_id'],
                impact_type=item['impact_type'],
                justification=item.get('justification'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now()
            )
            self.db_session.add(candidate)
            count += 1
        return count

    def _import_arch_solutions(self, data: List[Dict]) -> int:
        """Импортирует архитектурные решения."""
        count = 0
        for item in data:
            existing = self.db_session.query(ArchSolution).filter(
                ArchSolution.id == item.get('id')
            ).first()

            if existing:
                continue

            arch = ArchSolution(
                id=item.get('id'),
                task_id=item['task_id'],
                solution_name=item['solution_name'],
                description=item['description'],
                approach=item.get('approach', 'monolith'),
                tech_stack=item.get('tech_stack', []),
                depends_on=item.get('depends_on'),
                replaces=item.get('replaces'),
                status=item.get('status', 'proposed'),
                created_by=item.get('created_by'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now(),
                is_active=item.get('is_active', True),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None
            )
            self.db_session.add(arch)
            count += 1
        return count

    def _import_arch_candidates(self, data: List[Dict]) -> int:
        """Импортирует кандидатов архитектуры."""
        from analitik_core.models import ArchCandidate
        count = 0
        for item in data:
            existing = self.db_session.query(ArchCandidate).filter(
                ArchCandidate.id == item.get('id')
            ).first()

            if existing:
                continue

            candidate = ArchCandidate(
                id=item.get('id'),
                arch_solution_id=item['arch_solution_id'],
                target_id=item['target_id'],
                impact_type=item['impact_type'],
                justification=item.get('justification'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now()
            )
            self.db_session.add(candidate)
            count += 1
        return count

    def _import_plans(self, data: List[Dict]) -> int:
        """Импортирует планы."""
        count = 0
        for item in data:
            existing = self.db_session.query(Plan).filter(
                Plan.id == item.get('id')
            ).first()

            if existing:
                continue

            plan = Plan(
                id=item.get('id'),
                arch_solution_id=item['arch_solution_id'],
                plan_name=item['plan_name'],
                description=item.get('description'),
                step_order=item['step_order'],
                depends_on=item.get('depends_on'),
                assignee=item.get('assignee'),
                status=item.get('status', 'pending'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now(),
                completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None,
                is_active=item.get('is_active', True),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None
            )
            self.db_session.add(plan)
            count += 1
        return count

    def _import_plan_candidates(self, data: List[Dict]) -> int:
        """Импортирует кандидатов планов."""
        from analitik_core.models import PlanCandidate
        count = 0
        for item in data:
            existing = self.db_session.query(PlanCandidate).filter(
                PlanCandidate.id == item.get('id')
            ).first()

            if existing:
                continue

            candidate = PlanCandidate(
                id=item.get('id'),
                plan_id=item['plan_id'],
                target_id=item['target_id'],
                impact_type=item['impact_type'],
                justification=item.get('justification'),
                created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else datetime.now()
            )
            self.db_session.add(candidate)
            count += 1
        return count

    def _import_actions(self, data: List[Dict]) -> int:
        """Импортирует действия."""
        count = 0
        for item in data:
            existing = self.db_session.query(Action).filter(
                Action.id == item.get('id')
            ).first()

            if existing:
                continue

            action = Action(
                id=item.get('id'),
                plan_id=item['plan_id'],
                action_order=item['action_order'],
                action_type=item['action_type'],
                change_description=item['change_description'],
                new_value=item.get('new_value'),
                precondition=item.get('precondition'),
                postcondition=item.get('postcondition'),
                executed_at=datetime.fromisoformat(item['executed_at']) if item.get('executed_at') else None,
                is_active=item.get('is_active', True),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None
            )
            self.db_session.add(action)
            count += 1
        return count

    def _import_action_results(self, data: List[Dict]) -> int:
        """Импортирует результаты действий."""
        count = 0
        for item in data:
            existing = self.db_session.query(ActionResult).filter(
                ActionResult.id == item.get('id')
            ).first()

            if existing:
                continue

            result = ActionResult(
                id=item.get('id'),
                action_id=item['action_id'],
                target_id=item['target_id'],
                change_type=item['change_type'],
                old_snapshot=item.get('old_snapshot'),
                new_snapshot=item.get('new_snapshot'),
                new_version_id=item.get('new_version_id'),
                executed_at=datetime.fromisoformat(item['executed_at']) if item.get('executed_at') else datetime.now()
            )
            self.db_session.add(result)
            count += 1
        return count

    def _import_calls(self, data: List[Dict]) -> int:
        """Импортирует вызовы."""
        count = 0
        for item in data:
            existing = self.db_session.query(Call).filter(
                Call.id == item.get('id')
            ).first()

            if existing:
                continue

            call = Call(
                id=item.get('id'),
                caller_entity_id=item['caller_entity_id'],
                callee_name=item['callee_name'],
                callee_type=item.get('callee_type', 'unknown'),
                line_number=item.get('line_number', 0),
                is_active=item.get('is_active', True),
                dt_start=datetime.fromisoformat(item['dt_start']) if item.get('dt_start') else datetime.now(),
                dt_end=datetime.fromisoformat(item['dt_end']) if item.get('dt_end') else None
            )
            self.db_session.add(call)
            count += 1
        return count


# ================================================================
# UI ДИАЛОГ ЭКСПОРТА/ИМПОРТА
# ================================================================

class ExportImportDialog(QDialog):
    """Диалог экспорта/импорта данных."""

    def __init__(self, parent=None, db_session=None):
        super().__init__(parent)
        self.db_session = db_session or get_session()
        self.manager = ExportImportManager(self.db_session)

        self.setWindowTitle("📦 Экспорт/Импорт данных")
        self.resize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Вкладки
        tabs = QTabWidget()

        # Вкладка экспорта
        export_tab = self._setup_export_tab()
        tabs.addTab(export_tab, "📤 Экспорт")

        # Вкладка импорта
        import_tab = self._setup_import_tab()
        tabs.addTab(import_tab, "📥 Импорт")

        layout.addWidget(tabs)

        # Кнопка закрытия
        btn_close = QPushButton("✖ Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _setup_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Настройки экспорта
        settings_group = QGroupBox("Настройки экспорта")
        settings_layout = QVBoxLayout(settings_group)

        self.chk_include_history = QCheckBox("Включить историю версий")
        self.chk_include_history.setChecked(True)
        settings_layout.addWidget(self.chk_include_history)

        self.chk_export_tasks = QCheckBox("Экспортировать задачи и архитектуру")
        self.chk_export_tasks.setChecked(True)
        settings_layout.addWidget(self.chk_export_tasks)

        self.chk_export_calls = QCheckBox("Экспортировать граф вызовов")
        self.chk_export_calls.setChecked(True)
        settings_layout.addWidget(self.chk_export_calls)

        layout.addWidget(settings_group)

        # Кнопки экспорта
        btn_group = QGroupBox("Действия")
        btn_layout = QVBoxLayout(btn_group)

        btn_export_all = QPushButton("📤 Экспортировать всё")
        btn_export_all.clicked.connect(self._export_all)
        btn_layout.addWidget(btn_export_all)

        btn_export_task = QPushButton("📋 Экспортировать задачу с сущностями")
        btn_export_task.clicked.connect(self._export_task)
        btn_layout.addWidget(btn_export_task)

        layout.addWidget(btn_group)

        layout.addStretch()
        return tab

    def _setup_import_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Настройки импорта
        settings_group = QGroupBox("Настройки импорта")
        settings_layout = QVBoxLayout(settings_group)

        self.chk_clear_existing = QCheckBox("Очистить существующие данные перед импортом")
        self.chk_clear_existing.setChecked(False)
        settings_layout.addWidget(self.chk_clear_existing)

        layout.addWidget(settings_group)

        # Кнопки импорта
        btn_group = QGroupBox("Действия")
        btn_layout = QVBoxLayout(btn_group)

        btn_import = QPushButton("📥 Импортировать из файла")
        btn_import.clicked.connect(self._import)
        btn_layout.addWidget(btn_import)

        layout.addWidget(btn_group)

        layout.addStretch()
        return tab

    def _export_all(self):
        """Экспортирует все данные."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить экспорт",
            f"analitik_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)"
        )

        if not file_path:
            return

        progress = QProgressDialog("Экспорт данных...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            data = self.manager.export_all(
                file_path,
                self.chk_include_history.isChecked(),
                self.chk_export_tasks.isChecked(),
                self.chk_export_calls.isChecked()
            )

            progress.close()

            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"✅ Экспортировано записей: {data['export_info']['total_records']}\n\n"
                f"Файл: {file_path}"
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _export_task(self):
        """Экспортирует задачу с сущностями."""
        # TODO: Диалог выбора задачи
        QMessageBox.information(self, "Информация", "Функция выбора задачи в разработке")

    def _import(self):
        """Импортирует данные."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для импорта",
            "",
            "JSON files (*.json)"
        )

        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Импортировать данные из файла?\n\n{file_path}\n\n"
            f"{'⚠️ Существующие данные будут удалены!' if self.chk_clear_existing.isChecked() else 'Данные будут добавлены к существующим.'}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog("Импорт данных...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            stats = self.manager.import_data(
                file_path,
                self.chk_clear_existing.isChecked()
            )

            progress.close()

            QMessageBox.information(
                self,
                "Импорт завершён",
                f"✅ Импортировано:\n\n"
                f"  📦 Сущностей: {stats['entities']}\n"
                f"  📋 Задач: {stats['tasks']}\n"
                f"  📎 Кандидатов задач: {stats['task_candidates']}\n"
                f"  📐 Архитектур: {stats['arch_solutions']}\n"
                f"  📎 Кандидатов архитектуры: {stats['arch_candidates']}\n"
                f"  📋 Планов: {stats['plans']}\n"
                f"  📎 Кандидатов планов: {stats['plan_candidates']}\n"
                f"  🔧 Действий: {stats['actions']}\n"
                f"  📊 Результатов: {stats['action_results']}\n"
                f"  📞 Вызовов: {stats['calls']}"
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))


# ================================================================
# ФУНКЦИЯ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_export_import_dialog(parent=None, db_session=None):
    """Показывает диалог экспорта/импорта."""
    dialog = ExportImportDialog(parent, db_session)
    return dialog.exec_()