# mozart_import/core/metadata_creator.py
from typing import Optional, List, Dict, Any
from database import DatabaseService
from .models import MatchedEntity, MatchedField, ImportProfile
from composition_manager import CompositionManager


class MetadataCreator:
    def __init__(self, db: DatabaseService):
        self.db = db
        self.comp_manager = CompositionManager(db=db)
        self.doc_class_id = self._get_class_id('DOC')
        self.dict_class_id = self._get_class_id('DICT')

    def _get_class_id(self, class_alias: str) -> Optional[int]:
        res = self.db.execute_query("SELECT id FROM meta.entity_classes WHERE calias = %s", (class_alias,))
        return res[0][0] if res else None

    def _create_entity_type(self, table_name: str, is_document: bool = False) -> int:
        cname = table_name.capitalize()
        calias = table_name.lower().replace(' ', '_')
        class_id = self.doc_class_id if is_document else self.dict_class_id
        sql = """
            INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        res = self.db.execute_query(sql, (
            cname, calias, class_id,
            'DOC' if is_document else '',
            False, False, True, 1, 1
        ))
        return res[0][0]

    def _create_field(self, entity_id: int, field_name: str, field_type: str, calias: str, ref_entity_id: Optional[int] = None) -> int:
        sql = """
            INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, lisindexed, ref_entitytypeid, status_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        res = self.db.execute_query(sql, (entity_id, field_name, field_type, calias, True, ref_entity_id, 1))
        field_id = res[0][0]
        self.db.execute_procedure("meta.p_field_sync", (field_id,))
        return field_id

    def ensure_entity_and_fields(self, matched_entity: MatchedEntity) -> int:
        if matched_entity.target_entity_id is not None and not matched_entity.is_new:
            entity_id = matched_entity.target_entity_id
        else:
            is_doc = matched_entity.is_document
            entity_id = self._create_entity_type(matched_entity.source_table, is_doc)
            matched_entity.target_entity_id = entity_id
            matched_entity.is_new = True

        for field in matched_entity.fields:
            if not field.target_field or field.target_field == '':
                source_field_info = None
                for src_field in getattr(matched_entity, 'source_table_fields', []):
                    if src_field.name == field.source_field:
                        source_field_info = src_field
                        break
                if source_field_info is None:
                    continue
                if field.is_reference:
                    mozart_type = 'R'
                    ref_entity = field.ref_entitytype_id
                elif source_field_info.field_type.name == 'INTEGER':
                    mozart_type = 'I'
                    ref_entity = None
                elif source_field_info.field_type.name == 'FLOAT':
                    mozart_type = 'N'
                    ref_entity = None
                else:
                    mozart_type = 'C'
                    ref_entity = None
                new_field_name = field.source_field.lower()
                new_calias = field.source_field.capitalize()
                self._create_field(entity_id, new_field_name, mozart_type, new_calias, ref_entity)
                field.target_field = new_field_name
                field.confidence = 1.0
        return entity_id

    def create_composition_if_needed(self, parent_entity_id: int, child_entity_id: int, link_field: str, role_id: int = None) -> bool:
        if role_id is None:
            roles = self.db.execute_query("SELECT id FROM meta.composition_roles WHERE calias = 'DEFAULT'")
            if roles:
                role_id = roles[0][0]
            else:
                res = self.db.execute_query(
                    "INSERT INTO meta.composition_roles (calias, cname) VALUES ('DEFAULT', 'Основная') RETURNING id"
                )
                role_id = res[0][0]
        exists = self.db.execute_query(
            "SELECT id FROM meta.entity_composition WHERE parent_entityid=%s AND child_entityid=%s AND role_id=%s",
            (parent_entity_id, child_entity_id, role_id)
        )
        if exists:
            return True
        return self.comp_manager.add_composition(parent_entity_id, child_entity_id, role_id, link_field, 10)