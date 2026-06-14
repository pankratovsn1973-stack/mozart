# mozart_import/core/mozart_matcher.py
from typing import List, Dict, Optional, Any, Tuple
from difflib import SequenceMatcher
from .models import SourceSchema, SourceTable, SourceField, FieldType
from .models import MatchedEntity, MatchedField, MappingProposal
from database import DatabaseService


class MozartMatcher:
    """
    Сопоставляет исходную схему (SourceSchema) с метаданными Mozart.
    Возвращает MappingProposal с предложениями по сущностям и полям.
    """

    def __init__(self, db: DatabaseService):
        self.db = db
        # Загружаем метаданные Mozart при инициализации
        self.entitytypes = {}  # {id: {cname, calias, class_id, class_alias, fields}}
        self._load_metadata()

    def _load_metadata(self):
        # Загружаем сущности
        rows = self.db.execute_query("""
            SELECT e.id, e.cname, e.calias, e.class_id, c.calias as class_alias
            FROM meta.entitytypes e
            JOIN meta.entity_classes c ON e.class_id = c.id
            ORDER BY e.cname
        """)
        for row in rows:
            eid, cname, calias, class_id, class_alias = row
            self.entitytypes[eid] = {
                'cname': cname,
                'calias': calias,
                'class_id': class_id,
                'class_alias': class_alias,
                'fields': {}
            }
        # Загружаем поля
        rows = self.db.execute_query("""
            SELECT f.entitytypeid, f.cfieldname, f.calias, f.cfieldtype,
                   f.ref_entitytypeid, ft.cname as type_name
            FROM meta.fields f
            JOIN meta.field_types ft ON f.cfieldtype = ft.ccode
            ORDER BY f.entitytypeid, f.isortorder
        """)
        for row in rows:
            eid, cfieldname, calias, cfieldtype, ref_eid, type_name = row
            if eid in self.entitytypes:
                self.entitytypes[eid]['fields'][cfieldname] = {
                    'calias': calias,
                    'cfieldtype': cfieldtype,
                    'ref_entitytypeid': ref_eid,
                    'type_name': type_name
                }

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _match_table_to_entity(self, table: SourceTable) -> Tuple[Optional[int], str, float]:
        """
        Пытается найти подходящую сущность в Mozart по имени таблицы.
        Возвращает (entity_id, entity_name, confidence)
        """
        best_id = None
        best_name = None
        best_score = 0.0
        for eid, info in self.entitytypes.items():
            score = max(self._similarity(table.name, info['cname']),
                        self._similarity(table.name, info['calias']))
            if score > best_score:
                best_score = score
                best_id = eid
                best_name = info['cname']
        if best_score > 0.6:
            return best_id, best_name, best_score
        return None, table.name, 0.0

    def _match_field_to_field(self, source_field: SourceField, target_fields: Dict) -> Tuple[Optional[str], float]:
        """
        Сопоставляет поле источника с полем сущности Mozart по имени и типу.
        Возвращает (target_field_name, confidence)
        """
        best_field = None
        best_score = 0.0
        for fname, finfo in target_fields.items():
            name_score = max(self._similarity(source_field.name, fname),
                             self._similarity(source_field.name, finfo['calias']))
            type_score = 1.0
            # Упрощённое соответствие типов
            if finfo['cfieldtype'] == 'C' and source_field.field_type == FieldType.STRING:
                type_score = 1.0
            elif finfo['cfieldtype'] == 'I' and source_field.field_type == FieldType.INTEGER:
                type_score = 1.0
            elif finfo['cfieldtype'] == 'N' and source_field.field_type == FieldType.FLOAT:
                type_score = 1.0
            elif finfo['cfieldtype'] == 'D' and source_field.field_type == FieldType.DATE:
                type_score = 1.0
            elif finfo['cfieldtype'] == 'L' and source_field.field_type == FieldType.BOOLEAN:
                type_score = 1.0
            else:
                type_score = 0.5
            total = (name_score * 0.7 + type_score * 0.3)
            if total > best_score:
                best_score = total
                best_field = fname
        if best_score > 0.5:
            return best_field, best_score
        return None, 0.0

    def propose(self, source_schema: SourceSchema) -> MappingProposal:
        """
        Строит MappingProposal для всей исходной схемы.
        """
        entities = []
        unresolved = []
        suggestions = []

        for table in source_schema.tables:
            entity_id, entity_name, conf = self._match_table_to_entity(table)
            if entity_id is not None:
                # Существующая сущность
                target_fields = self.entitytypes[entity_id]['fields']
                matched_fields = []
                for src_field in table.fields:
                    target_field, fconf = self._match_field_to_field(src_field, target_fields)
                    if target_field:
                        is_ref = (target_fields[target_field]['cfieldtype'] == 'R')
                        ref_entity = target_fields[target_field]['ref_entitytypeid']
                        matched_fields.append(MatchedField(
                            source_field=src_field.name,
                            target_field=target_field,
                            confidence=fconf,
                            is_reference=is_ref,
                            ref_entitytype_id=ref_entity
                        ))
                    else:
                        # Поле не найдено, предлагаем добавить
                        matched_fields.append(MatchedField(
                            source_field=src_field.name,
                            target_field='',  # будет новое
                            confidence=0.0,
                            is_reference=False
                        ))
                entities.append(MatchedEntity(
                    source_table=table.name,
                    target_entity_id=entity_id,
                    target_entity_name=entity_name,
                    confidence=conf,
                    fields=matched_fields,
                    is_new=False
                ))
            else:
                # Новая сущность
                unresolved.append(table.name)
                suggestions.append(table.name)

        return MappingProposal(
            source_schema=source_schema,
            entities=entities,
            unresolved_tables=unresolved,
            suggestions_for_new_entities=suggestions
        )