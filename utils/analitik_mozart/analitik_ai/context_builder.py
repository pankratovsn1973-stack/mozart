# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ai/context_builder.py
"""
Генератор контекста для ИИ-ассистента.
Версия: 2.0 — для единой таблицы сущностей
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import text

from analitik_core.database import get_session, get_db
from analitik_core.models import Entity, EntityType, Task, TaskCandidate


class ContextBuilder:
    """
    Строитель контекста для ИИ-запросов.
    Собирает данные из БД и формирует промпт для человека.
    """

    def __init__(self, db_session=None, view_time: Optional[datetime] = None):
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.view_time = view_time or datetime.now()

    # ================================================================
    # ГЕНЕРАЦИЯ ПРОМПТА
    # ================================================================

    def build_prompt_from_task(self, task_id: str) -> str:
        """
        Формирует промпт на основе задачи и привязанных к ней сущностей.
        """
        # Получаем задачу
        task = self.db_session.query(Task).filter(
            Task.id == task_id,
            Task.is_active == True
        ).first()

        if not task:
            return "❌ Ошибка: Задача не найдена."

        prompt_parts = []
        prompt_parts.append("=" * 60)
        prompt_parts.append(f"ЗАДАЧА: {task.task_number} - {task.title}")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")
        prompt_parts.append(f"Описание задачи:")
        prompt_parts.append(task.description)
        prompt_parts.append("")
        prompt_parts.append(f"Приоритет: {task.priority}")
        prompt_parts.append(f"Статус: {task.status}")
        prompt_parts.append("")

        # Получаем привязанные сущности (кандидаты)
        candidates = self.db_session.query(TaskCandidate).filter(
            TaskCandidate.task_id == task_id,
            TaskCandidate.is_active == True
        ).all()

        if candidates:
            prompt_parts.append("-" * 40)
            prompt_parts.append("СВЯЗАННЫЕ СУЩНОСТИ (кандидаты на изменение):")
            prompt_parts.append("-" * 40)

            for candidate in candidates:
                entity = self.db_session.query(Entity).filter(
                    Entity.id == candidate.target_id,
                    Entity.is_active == True
                ).first()

                if entity:
                    prompt_parts.append("")
                    prompt_parts.append(f"📌 {EntityType.get_icon(entity.type_id)} {entity.c_name}")
                    prompt_parts.append(f"   Тип: {EntityType.get_name(entity.type_id)}")
                    prompt_parts.append(f"   Воздействие: {candidate.impact_type}")
                    if candidate.justification:
                        prompt_parts.append(f"   Обоснование: {candidate.justification}")

                    # Добавляем код сущности
                    if entity.t_blobskript:
                        prompt_parts.append("")
                        prompt_parts.append("```python")
                        prompt_parts.append(entity.t_blobskript)
                        prompt_parts.append("```")
                    else:
                        # Если нет кода, показываем данные
                        if entity.j_data:
                            prompt_parts.append(f"   Данные: {entity.j_data}")

                    # Если есть комментарий
                    if entity.m_comment:
                        prompt_parts.append(f"   Описание: {entity.m_comment}")

                    # Для методов и процедур показываем параметры
                    if entity.type_id in (EntityType.METHOD, EntityType.PROCEDURE):
                        params = self.db_session.query(Entity).filter(
                            Entity.type_id == EntityType.PARAMETER,
                            Entity.parent_id == entity.id,
                            Entity.is_active == True
                        ).order_by(Entity.n_order).all()

                        if params:
                            prompt_parts.append("   Параметры:")
                            for param in params:
                                p_type = param.j_data.get('param_type', 'Any') if param.j_data else 'Any'
                                default = param.j_data.get('default_value') if param.j_data else None
                                required = param.j_data.get('is_required', True) if param.j_data else True
                                prompt_parts.append(
                                    f"     - {param.c_name}: {p_type}"
                                    f"{'' if required else f' = {default}'}"
                                )

                    # Для классов показываем методы
                    if entity.type_id == EntityType.CLASS:
                        methods = self.db_session.query(Entity).filter(
                            Entity.type_id == EntityType.METHOD,
                            Entity.parent_id == entity.id,
                            Entity.is_active == True
                        ).order_by(Entity.n_order).all()

                        if methods:
                            prompt_parts.append("   Методы:")
                            for method in methods:
                                m_type = method.j_data.get('method_type', 'instance') if method.j_data else 'instance'
                                prompt_parts.append(f"     - {method.c_name}() ({m_type})")

        prompt_parts.append("")
        prompt_parts.append("=" * 60)
        prompt_parts.append("ЗАДАНИЕ ДЛЯ ИИ:")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")
        prompt_parts.append("Проанализируй задачу и предоставленные сущности.")
        prompt_parts.append("Предложи изменения в коде для решения задачи.")
        prompt_parts.append("")
        prompt_parts.append("Требования:")
        prompt_parts.append("1. Сохраняй существующую сигнатуру методов/процедур")
        prompt_parts.append("2. Используй типизацию Python")
        prompt_parts.append("3. Добавь докстринги")
        prompt_parts.append("4. Верни ТОЛЬКО обновленный код (без пояснений)")

        return "\n".join(prompt_parts)

    def build_prompt_from_entity(self, entity_id: str, task_description: str = "") -> str:
        """
        Формирует промпт на основе конкретной сущности.
        """
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return "❌ Ошибка: Сущность не найдена."

        prompt_parts = []
        prompt_parts.append("=" * 60)
        prompt_parts.append(f"СУЩНОСТЬ: {entity.c_name}")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")
        prompt_parts.append(f"Тип: {EntityType.get_name(entity.type_id)}")
        prompt_parts.append(f"ID: {entity.id}")

        if task_description:
            prompt_parts.append("")
            prompt_parts.append(f"ЗАДАЧА: {task_description}")

        prompt_parts.append("")
        prompt_parts.append("-" * 40)
        prompt_parts.append("КОД:")
        prompt_parts.append("-" * 40)

        if entity.t_blobskript:
            prompt_parts.append("```python")
            prompt_parts.append(entity.t_blobskript)
            prompt_parts.append("```")
        else:
            prompt_parts.append("(код отсутствует)")

        if entity.m_comment:
            prompt_parts.append("")
            prompt_parts.append(f"Описание: {entity.m_comment}")

        if entity.j_data:
            prompt_parts.append("")
            prompt_parts.append(f"Данные: {entity.j_data}")

        # Для методов и процедур показываем параметры
        if entity.type_id in (EntityType.METHOD, EntityType.PROCEDURE):
            params = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.PARAMETER,
                Entity.parent_id == entity.id,
                Entity.is_active == True
            ).order_by(Entity.n_order).all()

            if params:
                prompt_parts.append("")
                prompt_parts.append("Параметры:")
                for param in params:
                    p_type = param.j_data.get('param_type', 'Any') if param.j_data else 'Any'
                    default = param.j_data.get('default_value') if param.j_data else None
                    required = param.j_data.get('is_required', True) if param.j_data else True
                    prompt_parts.append(
                        f"  - {param.c_name}: {p_type}"
                        f"{'' if required else f' = {default}'}"
                    )

        # Для класса показываем методы и свойства
        if entity.type_id == EntityType.CLASS:
            children = self.db_session.query(Entity).filter(
                Entity.parent_id == entity.id,
                Entity.is_active == True
            ).order_by(Entity.type_id, Entity.n_order).all()

            if children:
                prompt_parts.append("")
                prompt_parts.append("Содержимое класса:")

                methods = [c for c in children if c.type_id == EntityType.METHOD]
                props = [c for c in children if c.type_id == EntityType.PROPERTY]
                vars_ = [c for c in children if c.type_id == EntityType.CLASS_VARIABLE]

                if vars_:
                    prompt_parts.append("  Переменные класса:")
                    for v in vars_:
                        v_type = v.j_data.get('var_type', 'Any') if v.j_data else 'Any'
                        prompt_parts.append(f"    - {v.c_name}: {v_type}")

                if props:
                    prompt_parts.append("  Свойства (@property):")
                    for p in props:
                        p_type = p.j_data.get('prop_type', 'Any') if p.j_data else 'Any'
                        readonly = p.j_data.get('is_readonly', True) if p.j_data else True
                        prompt_parts.append(f"    - {p.c_name}: {p_type} {'(readonly)' if readonly else ''}")

                if methods:
                    prompt_parts.append("  Методы:")
                    for m in methods:
                        m_type = m.j_data.get('method_type', 'instance') if m.j_data else 'instance'
                        prompt_parts.append(f"    - {m.c_name}() ({m_type})")

        prompt_parts.append("")
        prompt_parts.append("=" * 60)
        prompt_parts.append("ЗАДАНИЕ ДЛЯ ИИ:")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")
        prompt_parts.append("Проанализируй сущность и предложи улучшения.")
        prompt_parts.append("Верни ТОЛЬКО обновленный код (без пояснений).")

        return "\n".join(prompt_parts)

    # ================================================================
    # ПАРСИНГ ОТВЕТА ИИ
    # ================================================================

    def parse_ai_response(self, response: str, entity_id: str) -> Dict[str, Any]:
        """
        Парсит ответ ИИ и пытается извлечь код для обновления сущности.
        """
        result = {
            'success': False,
            'entity_id': entity_id,
            'new_code': None,
            'error': None,
            'changes': []
        }

        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            result['error'] = 'Сущность не найдена'
            return result

        # Пытаемся извлечь код из ответа
        code = self._extract_code(response)

        if not code:
            result['error'] = 'Не удалось извлечь код из ответа ИИ'
            return result

        result['new_code'] = code
        result['success'] = True

        # Сравниваем с текущим кодом
        if entity.t_blobskript != code:
            result['changes'].append({
                'type': 'modified',
                'entity': entity.c_name,
                'old_code': entity.t_blobskript,
                'new_code': code
            })

        return result

    def _extract_code(self, response: str) -> Optional[str]:
        """
        Извлекает код из ответа ИИ.
        Ищет блоки ```python ... ``` или просто код без маркеров.
        """
        import re

        # Ищем блоки с python
        pattern = r'```(?:python|py)\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            # Берем самый большой блок (обычно это основной код)
            return max(matches, key=len).strip()

        # Ищем любые блоки кода
        pattern = r'```\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return max(matches, key=len).strip()

        # Если нет блоков, но есть явный код (начинается с def или class)
        lines = response.strip().split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('def ', 'class ', 'async def ')):
                in_code = True
            if in_code:
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines)

        return None

    # ================================================================
    # ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ
    # ================================================================

    def apply_changes(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применяет изменения, извлечённые из ответа ИИ.
        """
        result = {
            'success': False,
            'message': '',
            'entity_id': None,
            'new_version_id': None,
            'error': None
        }

        if not parse_result.get('success'):
            result['error'] = parse_result.get('error', 'Не удалось распарсить ответ')
            return result

        entity_id = parse_result.get('entity_id')
        new_code = parse_result.get('new_code')

        if not entity_id or not new_code:
            result['error'] = 'Отсутствует ID сущности или новый код'
            return result

        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            result['error'] = 'Сущность не найдена'
            return result

        # Закрываем старую версию
        entity.is_active = False
        entity.dt_end = datetime.now()

        # Создаём новую версию
        new_entity = Entity(
            type_id=entity.type_id,
            c_name=entity.c_name,
            parent_id=entity.parent_id,
            t_blobskript=new_code,
            n_order=entity.n_order,
            j_data=entity.j_data.copy() if entity.j_data else {},
            m_comment=entity.m_comment,
            n_relise=entity.n_relise,
            n_old_version=entity.id
        )

        self.db_session.add(new_entity)
        self.db_session.flush()

        result['success'] = True
        result['message'] = f'✅ Сущность "{entity.c_name}" обновлена'
        result['entity_id'] = str(entity.id)
        result['new_version_id'] = str(new_entity.id)

        self.db_session.commit()

        return result