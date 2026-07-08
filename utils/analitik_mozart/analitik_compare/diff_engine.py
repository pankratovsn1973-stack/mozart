# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_compare/diff_engine.py
"""
Движок сравнения кода из БД и с диска.
Версия: 2.2 — для файлов используется t_full_text
"""

import difflib
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from analitik_core.database import get_db, get_session
from analitik_core.models import Entity, EntityType


class DiffEngine:
    """Движок сравнения кода из БД и с диска."""

    def __init__(self, db_session=None):
        self.db_session = db_session or get_session()
        self.db = get_db()

    def get_entity_code_from_db(self, entity_id: str, view_time: datetime = None) -> Optional[str]:
        """
        Получает код сущности из БД.
        Для файла — берёт t_full_text.
        Для остальных — t_blobskript.
        """
        dt = view_time or datetime.now()

        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return None

        # ============================================================
        # ДЛЯ ФАЙЛА — БЕРЁМ t_full_text
        # ============================================================
        if entity.type_id == EntityType.FILE:
            return entity.t_full_text

        # ============================================================
        # ДЛЯ ВСЕХ ОСТАЛЬНЫХ — t_blobskript
        # ============================================================
        return entity.t_blobskript

    def get_entity_code_from_disk(self, entity_id: str) -> Optional[str]:
        """
        Получает код сущности с диска.
        Для файла — читает файл целиком.
        Для остальных — находит родительский файл и извлекает нужную часть.
        """
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return None

        # ============================================================
        # ДЛЯ ФАЙЛА — ЧИТАЕМ С ДИСКА
        # ============================================================
        if entity.type_id == EntityType.FILE:
            full_path = entity.j_data.get('full_path') if entity.j_data else None
            if not full_path or not os.path.exists(full_path):
                return None
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None

        # ============================================================
        # ДЛЯ ОСТАЛЬНЫХ — ИЗВЛЕКАЕМ ИЗ ФАЙЛА
        # ============================================================
        file_entity = self._get_file_entity(entity)
        if not file_entity:
            return None

        full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None
        if not full_path or not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._extract_entity_from_content(content, entity)
        except Exception:
            return None

    def _get_file_entity(self, entity: Entity) -> Optional[Entity]:
        """Находит файл-родитель для сущности."""
        current = entity
        while current:
            if current.type_id == EntityType.FILE:
                return current
            if current.parent_id:
                current = self.db_session.query(Entity).filter(
                    Entity.id == current.parent_id,
                    Entity.is_active == True
                ).first()
            else:
                break
        return None

    def _extract_entity_from_content(self, content: str, entity: Entity) -> Optional[str]:
        """Извлекает код сущности из содержимого файла."""
        lines = content.split('\n')
        name = entity.c_name
        type_id = entity.type_id

        # Определяем паттерн поиска
        if type_id == EntityType.CLASS:
            pattern = f"class {name}"
        elif type_id in (EntityType.PROCEDURE, EntityType.METHOD):
            pattern = f"def {name}"
            if entity.j_data and entity.j_data.get('is_async'):
                pattern = f"async def {name}"
        elif type_id == EntityType.PROPERTY:
            pattern = f"@property"
        else:
            return None

        # Ищем начало
        start_idx = -1
        indent = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(pattern):
                start_idx = i
                indent = len(line) - len(stripped)
                break

        if start_idx == -1:
            return None

        # Ищем конец (следующая строка с тем же или меньшим отступом)
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip():
                cur_indent = len(lines[i]) - len(lines[i].lstrip())
                if cur_indent <= indent:
                    end_idx = i
                    break

        return '\n'.join(lines[start_idx:end_idx])

    # ================================================================
    # СРАВНЕНИЕ
    # ================================================================

    def compare(self, db_content: str, disk_content: str) -> Dict:
        """Сравнивает два содержимого."""
        if db_content is None and disk_content is None:
            return {'error': 'Оба источника пусты'}

        if db_content is None:
            return {
                'status': 'new',
                'analysis': 'Сущность существует только на диске',
                'stats': {'added': len(disk_content.splitlines()), 'deleted': 0, 'changed': 0}
            }

        if disk_content is None:
            return {
                'status': 'deleted',
                'analysis': 'Сущность существует только в БД',
                'stats': {'added': 0, 'deleted': len(db_content.splitlines()), 'changed': 0}
            }

        db_lines = db_content.splitlines()
        disk_lines = disk_content.splitlines()

        diff = difflib.unified_diff(
            db_lines, disk_lines,
            fromfile='База данных',
            tofile='Файл на диске',
            lineterm=''
        )

        diff_text = '\n'.join(diff)
        added, deleted, changed = self._analyze_diff(db_lines, disk_lines)
        changed_lines = self._find_changed_lines(db_lines, disk_lines)

        return {
            'status': 'modified' if (added or deleted or changed) else 'identical',
            'analysis': self._generate_analysis(added, deleted, changed, changed_lines),
            'stats': {
                'added': added,
                'deleted': deleted,
                'changed': changed,
                'total_diff': added + deleted + changed
            },
            'changed_lines': changed_lines,
            'diff_text': diff_text,
            'db_lines': db_lines,
            'disk_lines': disk_lines
        }

    def _analyze_diff(self, db_lines: List[str], disk_lines: List[str]) -> Tuple[int, int, int]:
        matcher = difflib.SequenceMatcher(None, db_lines, disk_lines)

        added, deleted, changed = 0, 0, 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                changed += max(i2 - i1, j2 - j1)
            elif tag == 'delete':
                deleted += i2 - i1
            elif tag == 'insert':
                added += j2 - j1

        return added, deleted, changed

    def _find_changed_lines(self, db_lines: List[str], disk_lines: List[str]) -> List[Dict]:
        changed = []
        matcher = difflib.SequenceMatcher(None, db_lines, disk_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                for idx in range(max(i2 - i1, j2 - j1)):
                    db_line = db_lines[i1 + idx] if i1 + idx < len(db_lines) else ''
                    disk_line = disk_lines[j1 + idx] if j1 + idx < len(disk_lines) else ''
                    changed.append({
                        'line_num': i1 + idx + 1,
                        'old': db_line,
                        'new': disk_line,
                        'type': 'changed'
                    })
            elif tag == 'delete':
                for idx in range(i2 - i1):
                    changed.append({
                        'line_num': i1 + idx + 1,
                        'old': db_lines[i1 + idx],
                        'new': '',
                        'type': 'deleted'
                    })
            elif tag == 'insert':
                for idx in range(j2 - j1):
                    changed.append({
                        'line_num': j1 + idx + 1,
                        'old': '',
                        'new': disk_lines[j1 + idx],
                        'type': 'added'
                    })

        return changed

    def _generate_analysis(self, added: int, deleted: int, changed: int, changed_lines: List[Dict]) -> str:
        parts = []

        if added == 0 and deleted == 0 and changed == 0:
            return "✅ Файлы идентичны"

        if added > 0:
            parts.append(f"➕ Добавлено строк: {added}")
        if deleted > 0:
            parts.append(f"➖ Удалено строк: {deleted}")
        if changed > 0:
            parts.append(f"✏️ Изменено строк: {changed}")

        if changed_lines:
            line_nums = sorted(set([cl['line_num'] for cl in changed_lines]))
            parts.append(f"📍 Строки: {', '.join(map(str, line_nums[:10]))}")
            if len(line_nums) > 10:
                parts.append(f"... и ещё {len(line_nums) - 10} строк")

        return " | ".join(parts)

    def compare_entity(self, entity_id: str, view_time: datetime = None) -> Dict:
        """Сравнивает сущность с диском."""
        dt = view_time or datetime.now()

        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return {'error': 'Сущность не найдена'}

        db_content = self.get_entity_code_from_db(entity_id, dt)
        disk_content = self.get_entity_code_from_disk(entity_id)

        result = self.compare(db_content, disk_content)

        result['entity_id'] = str(entity.id)
        result['entity_name'] = entity.c_name
        result['entity_type'] = EntityType.get_name(entity.type_id)
        result['entity_type_id'] = entity.type_id

        return result