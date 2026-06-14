# mozart_import/core/import_engine.py
# -*- coding: utf-8 -*-

import hashlib
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, date
from database import DatabaseService
from .models import ImportProfile, MatchedEntity
from .metadata_creator import MetadataCreator
from ..connectors.base_connector import BaseConnector


class ImportEngine:
    def __init__(self, db: DatabaseService, connector: BaseConnector, profile: ImportProfile):
        self.db = db
        self.connector = connector
        self.profile = profile
        self.meta_creator = MetadataCreator(db)
        self._reference_cache = {}
        self._source_id_field = 'sourceid'
        self._hash_field = 'data_hash'

    # -----------------------------------------------------------------
    # Работа с ext-таблицами и служебными колонками
    # -----------------------------------------------------------------
    def _ensure_system_columns(self, ext_table: str, alias: str):
        """Проверяет и добавляет служебные колонки в существующую таблицу."""
        # sourceid
        col_check = self.db.execute_query(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name='sourceid'",
            (f"ext_{alias}",)
        )
        if not col_check:
            self.db.execute_query(f"ALTER TABLE {ext_table} ADD COLUMN sourceid TEXT", fetch=False)
            self.db.execute_query(f"CREATE INDEX IF NOT EXISTS ix_{alias}_sourceid ON {ext_table} (sourceid)",
                                  fetch=False)

        # data_hash
        col_check = self.db.execute_query(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name='data_hash'",
            (f"ext_{alias}",)
        )
        if not col_check:
            self.db.execute_query(f"ALTER TABLE {ext_table} ADD COLUMN data_hash varchar(32)", fetch=False)

    def _ensure_ext_table(self, entity_id: int, entity_cname: str) -> str:
        """Проверяет существование ext-таблицы, создаёт при необходимости."""
        ext_table = f"ext.ext_{entity_cname.lower()}"
        check = self.db.execute_query("SELECT to_regclass(%s)", (ext_table,))

        if check and check[0][0]:
            self._ensure_system_columns(ext_table, entity_cname.lower())
            return ext_table

        sql = f"""
            CREATE TABLE {ext_table} (
                id SERIAL PRIMARY KEY,
                versionid INTEGER NOT NULL REFERENCES data.entity_versions(id) ON DELETE CASCADE
            )
        """
        self.db.execute_query(sql, fetch=False)
        self._ensure_system_columns(ext_table, entity_cname.lower())

        return ext_table

    def _get_ext_table(self, entity_id: int) -> Optional[str]:
        res = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (entity_id,))
        if not res:
            return None
        cname = res[0][0]
        return self._ensure_ext_table(entity_id, cname)

    def _ensure_sourceid_field(self, entity_id: int):
        """Создаёт поле sourceid в meta.fields (как служебное, is_system=True)."""
        exists = self.db.execute_query(
            "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
            (entity_id, self._source_id_field)
        )
        if not exists:
            self.db.execute_query(
                """INSERT INTO meta.fields 
                   (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id, is_system)
                   VALUES (%s, %s, 'C', 'Source ID', 255, True, 1, True)
                   RETURNING id""",
                (entity_id, self._source_id_field)
            )

    # -----------------------------------------------------------------
    # Хэширование данных
    # -----------------------------------------------------------------
    def _calculate_hash(self, values: Dict[str, Any], fields_map: Dict[str, str]) -> str:
        """Вычисляет MD5-хэш от значений всех маппинговых полей (кроме sourceid)."""
        hash_data = []
        for mozart_field, source_field in fields_map.items():
            if mozart_field == self._source_id_field:
                continue
            val = values.get(source_field)
            if val is None:
                hash_data.append("NULL")
            elif isinstance(val, (datetime, date)):
                hash_data.append(val.isoformat())
            else:
                hash_data.append(str(val))
        hash_string = "|".join(hash_data)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def _get_stored_hash(self, ext_table: str, source_id: str) -> Optional[str]:
        """Возвращает сохранённый хэш данных для записи с указанным sourceid."""
        res = self.db.execute_query(
            f"SELECT {self._hash_field} FROM {ext_table} WHERE sourceid = %s",
            (source_id,)
        )
        return res[0][0] if res else None

    def _update_hash(self, ext_table: str, version_id: int, new_hash: str):
        """Обновляет хэш в версии (при создании новой версии)."""
        self.db.execute_query(
            f"UPDATE {ext_table} SET {self._hash_field} = %s WHERE versionid = %s",
            (new_hash, version_id), fetch=False
        )

    # -----------------------------------------------------------------
    # Основные операции с инстансами и версиями
    # -----------------------------------------------------------------
    def _create_instance(self, entity_id: int) -> int:
        res = self.db.execute_query(
            "INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (%s, now()) RETURNING id",
            (entity_id,)
        )
        return res[0][0]

    def _create_version(self, instance_id: int, entity_id: int, values: Dict[str, Any],
                        fields_map: Dict[str, str], stats: Dict[str, int], source_id: Optional[str] = None):
        cname = values.get('cname', f"Импорт {datetime.now()}")
        res = self.db.execute_query(
            """INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start)
               VALUES (%s, %s, 'Active', now()) RETURNING id""",
            (instance_id, cname)
        )
        version_id = res[0][0]

        ext_table = self._get_ext_table(entity_id)
        if not ext_table:
            raise RuntimeError(f"Нет ext-таблицы для entity_id={entity_id}")

        columns = ['versionid']
        placeholders = ['%s']
        params = [version_id]

        if source_id is not None:
            columns.append(self._source_id_field)
            placeholders.append('%s')
            params.append(source_id)

        data_hash = self._calculate_hash(values, fields_map)
        columns.append(self._hash_field)
        placeholders.append('%s')
        params.append(data_hash)

        for mozart_field, source_field in fields_map.items():
            if mozart_field == self._source_id_field:
                continue
            columns.append(mozart_field)
            placeholders.append('%s')
            params.append(values.get(source_field))

        sql = f"INSERT INTO {ext_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        self.db.execute_query(sql, params, fetch=False)
        stats['inserted'] += 1

    def _update_version(self, instance_id: int, entity_id: int, values: Dict[str, Any],
                        fields_map: Dict[str, str], stats: Dict[str, int]):
        self.db.execute_query(
            "UPDATE data.entity_versions SET tdt_end = now(), cversionstatus = 'History' WHERE instanceid = %s AND cversionstatus = 'Active'",
            (instance_id,)
        )
        self._create_version(instance_id, entity_id, values, fields_map, stats, None)

    def _find_instance_by_sourceid(self, entity_id: int, source_id: str) -> Optional[int]:
        ext_table = self._get_ext_table(entity_id)
        if not ext_table:
            return None
        res = self.db.execute_query(
            f"SELECT v.instanceid FROM data.entity_versions v "
            f"JOIN {ext_table} e ON v.id = e.versionid "
            f"WHERE e.{self._source_id_field} = %s AND v.cversionstatus = 'Active'",
            (source_id,)
        )
        return res[0][0] if res else None

    def _get_or_create_instance(self, entity_id: int, source_id: Optional[str],
                                values: Dict[str, Any], fields_map: Dict[str, str],
                                stats: Dict[str, int]) -> Optional[int]:
        if source_id:
            existing = self._find_instance_by_sourceid(entity_id, source_id)
            if existing:
                ext_table = self._get_ext_table(entity_id)
                new_hash = self._calculate_hash(values, fields_map)
                old_hash = self._get_stored_hash(ext_table, source_id)

                if self.profile.import_mode == 'append':
                    stats['skipped'] += 1
                    return None

                elif self.profile.import_mode == 'full_update':
                    if new_hash == old_hash:
                        stats['skipped'] += 1
                        return None
                    else:
                        self._update_version(existing, entity_id, values, fields_map, stats)
                        stats['updated'] += 1
                        return existing
                else:
                    self._update_version(existing, entity_id, values, fields_map, stats)
                    stats['updated'] += 1
                    return existing

        instance_id = self._create_instance(entity_id)
        self._create_version(instance_id, entity_id, values, fields_map, stats, source_id)
        return instance_id

    # -----------------------------------------------------------------
    # Публичный метод для оркестратора
    # -----------------------------------------------------------------
    def import_single_entity(self, entity: MatchedEntity,
                             ref_rules: List[Dict[str, Any]],
                             instance_cache: Dict[str, Dict[str, int]]) -> (Dict[str, int], Dict[str, int]):
        entity_id = entity.target_entity_id
        if not entity_id:
            return {'inserted': 0, 'updated': 0, 'errors': 0, 'skipped': 0}, {}

        self._ensure_sourceid_field(entity_id)

        fields_map = {}
        ref_resolvers = []
        for field in entity.fields:
            fields_map[field.target_field] = field.source_field
            for rule in ref_rules:
                if rule['target_field'] == field.target_field:
                    ref_resolvers.append((field.target_field, rule['ref_entity_id'], rule['ref_key_field']))
                    break

        source_id_field = entity.source_id_field
        mapping_cache = {}
        stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'skipped': 0, 'details': []}

        for batch_num, batch in enumerate(self.connector.iter_records(entity.source_table, batch_size=100)):
            for record in batch:
                for tgt_field, ref_entity, ref_key_field in ref_resolvers:
                    key = record.get(ref_key_field)
                    if key:
                        record[fields_map[tgt_field]] = instance_cache.get(ref_entity, {}).get(str(key))
                    else:
                        record[fields_map[tgt_field]] = None

                source_id = None
                if source_id_field:
                    raw = record.get(source_id_field)
                    if raw is not None and str(raw).lower() != 'none':
                        source_id = str(raw)

                try:
                    instance_id = self._get_or_create_instance(entity_id, source_id, record, fields_map, stats)
                    if source_id and instance_id is not None:
                        mapping_cache[source_id] = instance_id
                except Exception as e:
                    stats['errors'] += 1
                    stats['details'].append(f"{entity.source_table}, source_id={source_id}: {e}")

        return {
            'inserted': stats['inserted'],
            'updated': stats['updated'],
            'errors': stats['errors'],
            'skipped': stats['skipped'],
            'details': stats['details']
        }, mapping_cache

    def run(self, progress_callback=None):
        raise NotImplementedError("Используйте ImportOrchestrator.run() или import_single_entity()")