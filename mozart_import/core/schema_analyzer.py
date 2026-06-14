# mozart_import/core/schema_analyzer.py
from typing import Dict, List, Optional, Any
from collections import Counter
from .models import SourceSchema, SourceTable, SourceField, FieldType


class SchemaAnalyzer:
    """
    Анализирует исходную схему, добавляет метаинформацию:
    - предполагаемые первичные ключи (по именам или уникальности)
    - предполагаемые внешние ключи (по именам полей)
    - статистику по полям (уникальность, заполненность)
    - кандидатов на иерархические связи (parent_id и т.п.)
    """

    def __init__(self, schema: SourceSchema):
        self.schema = schema
        self._analyze()

    def _analyze(self):
        for table in self.schema.tables:
            self._analyze_table(table)

    def _analyze_table(self, table: SourceTable):
        # 1. Определяем вероятный первичный ключ
        pk_candidates = []
        for field in table.fields:
            if field.is_primary_key:
                pk_candidates.append(field.name)
            elif field.name.lower() in ('id', 'code', 'num', 'number', 'key'):
                pk_candidates.append(field.name)
        if pk_candidates:
            table.primary_key = pk_candidates
        else:
            # если нет очевидного, предлагаем первый подходящий по типу целочисленный
            int_fields = [f.name for f in table.fields if f.field_type in (FieldType.INTEGER)]
            if int_fields:
                table.primary_key = [int_fields[0]]

        # 2. Определяем вероятные внешние ключи (по именам)
        fk_candidates = {}
        for field in table.fields:
            name_lower = field.name.lower()
            if name_lower.endswith('_id') or name_lower.startswith('id_') or name_lower in ('parentid', 'parent_id'):
                # предполагаем, что ссылается на таблицу без последнего суффикса
                target_table = name_lower.replace('_id', '').replace('id_', '')
                if target_table == 'parent':
                    target_table = table.name  # ссылка на саму себя (иерархия)
                fk_candidates[field.name] = target_table
        table.foreign_keys = fk_candidates

        # 3. Собираем статистику по полям (если есть sample_rows)
        if table.sample_rows:
            for field in table.fields:
                values = [row.get(field.name) for row in table.sample_rows if row.get(field.name) is not None]
                field.nullable = len(values) < len(table.sample_rows)
                # уникальность можно оценить на основе sample
                unique_vals = len(set(values))
                if unique_vals > 0 and len(values) > 0:
                    uniqueness = unique_vals / len(values)
                    # если в sample все значения уникальны, предполагаем, что поле уникально
                    if uniqueness == 1.0 and len(values) == len(table.sample_rows):
                        # помечаем как возможный кандидат на ключ
                        if not table.primary_key:
                            table.primary_key = [field.name]

    def get_primary_key_candidates(self, table_name: str) -> List[str]:
        for table in self.schema.tables:
            if table.name == table_name and table.primary_key:
                return table.primary_key
        return []

    def get_foreign_key_candidates(self, table_name: str) -> Dict[str, str]:
        for table in self.schema.tables:
            if table.name == table_name:
                return table.foreign_keys
        return {}

    def suggest_hierarchy_field(self, table_name: str) -> Optional[str]:
        """Возвращает имя поля, вероятно, указывающего на родителя (для иерархий)."""
        for table in self.schema.tables:
            if table.name == table_name:
                for field in table.fields:
                    name_lower = field.name.lower()
                    if name_lower in ('parentid', 'parent_id', 'pid', 'parent'):
                        return field.name
        return None

    def suggest_reference(self, field_name: str) -> Optional[str]:
        """По имени поля предполагает целевую сущность для внешней ссылки."""
        name_lower = field_name.lower()
        if name_lower.endswith('_id'):
            target = name_lower[:-3]
        elif name_lower.startswith('id_'):
            target = name_lower[3:]
        else:
            return None
        # ищем в схеме таблицу с таким именем
        for table in self.schema.tables:
            if table.name.lower() == target:
                return table.name
        return target  # не найдено, но возвращаем предположение