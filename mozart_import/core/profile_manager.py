# mozart_import/core/profile_manager.py
# -*- coding: utf-8 -*-

import json
from typing import Optional, List
from database import DatabaseService
from .models import ImportProfile, SourceType


class ProfileManager:
    def __init__(self, db: DatabaseService):
        self.db = db

    def save_profile(self, profile: ImportProfile) -> int:
        source_type_code = profile.source_type.value if profile.source_type else None

        # 1. Сохраняем или обновляем основной профиль
        if profile.id:
            self.db.execute_query("""
                UPDATE meta.import_profiles
                SET profile_name=%s, source_type=%s, source_path=%s,
                    file_format=%s, db_type=%s, db_host=%s, db_port=%s,
                    db_name=%s, db_user=%s, db_pass=%s, import_mode=%s,
                    updated_at=now()
                WHERE id=%s
            """, (profile.name, source_type_code, profile.source_path,
                  profile.file_format, profile.db_type, profile.db_host,
                  profile.db_port, profile.db_name, profile.db_user,
                  profile.db_pass, profile.import_mode, profile.id), fetch=False)
            # Удаляем старые связанные данные
            self.db.execute_query("DELETE FROM meta.import_source_links WHERE profile_id=%s", (profile.id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.import_mappings WHERE link_id IN (SELECT id FROM meta.import_links WHERE profile_id=%s)", (profile.id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.import_links WHERE profile_id=%s", (profile.id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.import_target_entities WHERE profile_id=%s", (profile.id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.import_source_references WHERE source_table_id IN (SELECT id FROM meta.import_source_tables WHERE profile_id=%s)", (profile.id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.import_source_tables WHERE profile_id=%s", (profile.id,), fetch=False)
        else:
            res = self.db.execute_query("""
                INSERT INTO meta.import_profiles
                    (profile_name, source_type, source_path, file_format,
                     db_type, db_host, db_port, db_name, db_user, db_pass, import_mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (profile.name, source_type_code, profile.source_path,
                  profile.file_format, profile.db_type, profile.db_host,
                  profile.db_port, profile.db_name, profile.db_user,
                  profile.db_pass, profile.import_mode))
            profile.id = res[0][0]

        # 2. Сохраняем таблицы источника
        source_table_ids = {}
        for table in profile.source_tables:
            res = self.db.execute_query("""
                INSERT INTO meta.import_source_tables (profile_id, table_name, row_count, sample_data)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (profile.id, table['name'], table.get('row_count'), json.dumps(table.get('sample_rows', []))))
            source_table_ids[table['name']] = res[0][0]

        # 3. Сохраняем целевые сущности
        target_entity_ids = {}
        for entity in profile.target_entities:
            res = self.db.execute_query("""
                INSERT INTO meta.import_target_entities (profile_id, entity_id, entity_name)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (profile.id, entity['id'], entity['name']))
            target_entity_ids[entity['id']] = res[0][0]

        # 4. Сохраняем связи и маппинги
        for link in profile.import_links:
            src_id = source_table_ids.get(link['source_table'])
            tgt_id = target_entity_ids.get(link['target_entity_id'])
            if src_id and tgt_id:
                res = self.db.execute_query("""
                    INSERT INTO meta.import_links (profile_id, source_table_id, target_entity_id)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (profile.id, src_id, tgt_id))
                link_id = res[0][0]
                self.db.execute_query("DELETE FROM meta.import_mappings WHERE link_id=%s", (link_id,), fetch=False)
                for mapping in link['mappings']:
                    self.db.execute_query("""
                        INSERT INTO meta.import_mappings
                            (link_id, source_field, target_field, field_type, field_length, is_source_id,
                             is_reference, ref_src_table, ref_src_key_field)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (link_id, source_field) DO UPDATE SET
                            target_field = EXCLUDED.target_field,
                            field_type = EXCLUDED.field_type,
                            field_length = EXCLUDED.field_length,
                            is_source_id = EXCLUDED.is_source_id,
                            is_reference = EXCLUDED.is_reference,
                            ref_src_table = EXCLUDED.ref_src_table,
                            ref_src_key_field = EXCLUDED.ref_src_key_field
                    """, (link_id, mapping['source_field'], mapping['target_field'],
                          mapping.get('field_type', 'C'), mapping.get('field_length', 255),
                          mapping.get('is_source_id', False),
                          mapping.get('is_reference', False),
                          mapping.get('ref_source_table', ''),
                          mapping.get('ref_source_key_field', '')), fetch=False)

        # 5. Сохраняем внутренние связи источника (FK)
        for fk in profile.source_fk_links:
            src_id = source_table_ids.get(fk['source_table'])
            ref_id = source_table_ids.get(fk['target_table'])
            if src_id and ref_id:
                self.db.execute_query("""
                    INSERT INTO meta.import_source_links (profile_id, source_table_id, source_field, ref_table_id, ref_field)
                    VALUES (%s, %s, %s, %s, %s)
                """, (profile.id, src_id, fk['source_field'], ref_id, fk['target_field']), fetch=False)

        # 6. Сохраняем перекрестные ссылки источника (source_references)
        for ref in profile.source_references:
            src_id = source_table_ids.get(ref['source_table'])
            dst_id = source_table_ids.get(ref['ref_table'])
            if src_id and dst_id:
                self.db.execute_query("""
                    INSERT INTO meta.import_source_references (source_table_id, source_field, ref_table_id, ref_key_field)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_table_id, source_field)
                    DO UPDATE SET ref_table_id = EXCLUDED.ref_table_id, ref_key_field = EXCLUDED.ref_key_field
                """, (src_id, ref['source_field'], dst_id, ref['ref_field']), fetch=False)

        return profile.id

    def load_profile(self, profile_id: int) -> Optional[ImportProfile]:
        rows = self.db.execute_query("""
            SELECT id, profile_name, source_type, source_path,
                   file_format, db_type, db_host, db_port, db_name, db_user, db_pass,
                   import_mode
            FROM meta.import_profiles
            WHERE id = %s
        """, (profile_id,))
        if not rows:
            return None
        row = rows[0]
        profile = ImportProfile(
            id=row[0],
            name=row[1],
            source_type=SourceType(row[2]),
            source_path=row[3],
            file_format=row[4],
            db_type=row[5],
            db_host=row[6],
            db_port=row[7],
            db_name=row[8],
            db_user=row[9],
            db_pass=row[10],
            import_mode=row[11] if len(row) > 11 else 'append'
        )

        source_tables = self.db.execute_query("""
            SELECT id, table_name, row_count, sample_data
            FROM meta.import_source_tables
            WHERE profile_id = %s
        """, (profile_id,))
        profile.source_tables = []
        source_table_map = {}
        for st in source_tables:
            tbl = {
                'id': st[0],
                'name': st[1],
                'row_count': st[2],
                'sample_rows': st[3] if st[3] else []
            }
            profile.source_tables.append(tbl)
            source_table_map[st[1]] = st[0]

        target_entities = self.db.execute_query("""
            SELECT id, entity_id, entity_name
            FROM meta.import_target_entities
            WHERE profile_id = %s
        """, (profile_id,))
        profile.target_entities = []
        target_entity_map = {}
        for te in target_entities:
            ent = {'id': te[1], 'name': te[2]}
            profile.target_entities.append(ent)
            target_entity_map[te[1]] = te[0]

        links = self.db.execute_query("""
            SELECT l.id, st.table_name, te.entity_id, te.entity_name
            FROM meta.import_links l
            JOIN meta.import_source_tables st ON l.source_table_id = st.id
            JOIN meta.import_target_entities te ON l.target_entity_id = te.id
            WHERE l.profile_id = %s
        """, (profile_id,))
        profile.import_links = []
        for link in links:
            mappings = self.db.execute_query("""
                SELECT source_field, target_field, field_type, field_length, is_source_id,
                       is_reference, ref_src_table, ref_src_key_field
                FROM meta.import_mappings
                WHERE link_id = %s
            """, (link[0],))
            profile.import_links.append({
                'source_table': link[1],
                'target_entity_id': link[2],
                'target_entity_name': link[3],
                'mappings': [{'source_field': m[0], 'target_field': m[1], 'field_type': m[2],
                              'field_length': m[3], 'is_source_id': m[4],
                              'is_reference': m[5], 'ref_source_table': m[6],
                              'ref_source_key_field': m[7]} for m in mappings]
            })

        source_fks = self.db.execute_query("""
            SELECT st1.table_name, ls.source_field, st2.table_name, ls.ref_field
            FROM meta.import_source_links ls
            JOIN meta.import_source_tables st1 ON ls.source_table_id = st1.id
            JOIN meta.import_source_tables st2 ON ls.ref_table_id = st2.id
            WHERE ls.profile_id = %s
        """, (profile_id,))
        profile.source_fk_links = [{'source_table': f[0], 'source_field': f[1],
                                    'target_table': f[2], 'target_field': f[3]} for f in source_fks]

        source_refs = self.db.execute_query("""
            SELECT st1.table_name, srf.source_field, st2.table_name, srf.ref_key_field
            FROM meta.import_source_references srf
            JOIN meta.import_source_tables st1 ON srf.source_table_id = st1.id
            JOIN meta.import_source_tables st2 ON srf.ref_table_id = st2.id
            WHERE st1.profile_id = %s
        """, (profile_id,))
        profile.source_references = [{'source_table': r[0], 'source_field': r[1],
                                      'ref_table': r[2], 'ref_field': r[3]} for r in source_refs]

        return profile

    def list_profiles(self) -> List[ImportProfile]:
        rows = self.db.execute_query("""
            SELECT id, profile_name, source_type, source_path
            FROM meta.import_profiles
            ORDER BY created_at DESC
        """)
        profiles = []
        for row in rows:
            profiles.append(ImportProfile(
                id=row[0],
                name=row[1],
                source_type=SourceType(row[2]),
                source_path=row[3]
            ))
        return profiles

    def delete_profile(self, profile_id: int):
        self.db.execute_query("DELETE FROM meta.import_profiles WHERE id=%s", (profile_id,), fetch=False)