# mozart_import/designer/entity_creator.py
# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional
from database import DatabaseService
from ..utils.field_creator import FieldCreator
from ..utils.ext_helper import ExtHelper
from lang.local_translator import LocalTranslator


class EntityCreator:
    """
    Создаёт новую сущность Mozart на основе таблицы источника.
    Копирует все отмеченные поля из источника в сущность.
    """
    def __init__(self, db: DatabaseService):
        self.db = db
        self.field_creator = FieldCreator(db)
        self.ext_helper = ExtHelper(db)
        self.translator = LocalTranslator()

    def create_entity_from_source(self,
                                  entity_name: str,
                                  entity_alias: str,
                                  class_id: int,
                                  source_table_name: str,
                                  checked_fields: list,    # список имён полей источника
                                  source_sample: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Создаёт тип сущности, ext-таблицу и поля meta.fields.
        Возвращает entity_id новой сущности.
        """
        # 1. Создаём запись в meta.entitytypes
        res = self.db.execute_query(
            """INSERT INTO meta.entitytypes
               (cname, calias, class_id, cbaseclass, lisversioned, isecuritystrategy, status_id)
               VALUES (%s, %s, %s, '', true, 1, 1) RETURNING id""",
            (entity_name, entity_alias, class_id)
        )
        if not res:
            return None
        entity_id = res[0][0]

        # 2. Обеспечиваем существование ext-таблицы
        self.ext_helper.ensure_ext_table(entity_id)

        # 3. Создаём поля
        fields_to_create = []
        for src_field in checked_fields:
            # Генерируем имя поля Mozart (латиница, без спецсимволов)
            from .designer_utils import to_field_name
            mozart_field = to_field_name(src_field)
            # Определяем тип по образцу (если есть)
            field_type = 'C'  # строка по умолчанию
            nlength = 255
            if source_sample and src_field in source_sample:
                val = source_sample[src_field]
                if isinstance(val, int):
                    field_type = 'I'
                    nlength = 0
                elif isinstance(val, float):
                    field_type = 'N'
                    nlength = 15
                elif isinstance(val, bool):
                    field_type = 'L'
                    nlength = 0
                else:
                    field_type = 'C'
                    nlength = max(255, len(str(val)) * 2)
            fields_to_create.append({
                'cfieldname': mozart_field,
                'cfieldtype': field_type,
                'calias': src_field.capitalize()[:50],
                'nlength': nlength,
                'lisindexed': True
            })
        if fields_to_create:
            self.field_creator.create_fields(entity_id, fields_to_create)

        return entity_id