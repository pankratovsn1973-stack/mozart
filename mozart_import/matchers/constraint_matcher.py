# mozart_import/matchers/constraint_matcher.py
from typing import List, Dict, Any


class ConstraintMatcher:
    """Сопоставление по ограничениям (первичные ключи, внешние ключи, уникальность)."""

    @staticmethod
    def is_primary_key_candidate(field_name: str) -> bool:
        """Проверяет, похоже ли имя поля на первичный ключ."""
        name_lower = field_name.lower()
        return name_lower in ('id', 'code', 'num', 'key', 'pk')

    @staticmethod
    def is_foreign_key_candidate(field_name: str) -> bool:
        """Проверяет, похоже ли имя поля на внешний ключ."""
        name_lower = field_name.lower()
        return name_lower.endswith('_id') or name_lower.startswith('id_') or name_lower in ('parentid', 'parent_id')

    @staticmethod
    def extract_referenced_table(field_name: str, current_table: str) -> str:
        """По имени внешнего ключа предполагает имя целевой таблицы."""
        name_lower = field_name.lower()
        if name_lower.endswith('_id'):
            target = name_lower[:-3]
        elif name_lower.startswith('id_'):
            target = name_lower[3:]
        else:
            target = name_lower
        if target == 'parent':
            target = current_table
        return target