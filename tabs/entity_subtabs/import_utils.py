# import_utils.py
from database import DatabaseService
from typing import Dict, Optional, List, Tuple


def get_entity_cname(db: DatabaseService, entitytype_id: int) -> Optional[str]:
    """Возвращает системное имя сущности (cname) по её ID."""
    res = db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (entitytype_id,))
    return res[0][0] if res else None


def ensure_sourceid_field(db: DatabaseService, entitytype_id: int, field_type: str = 'C', length: int = 100) -> None:
    """
    Проверяет наличие поля sourceid в ext-таблице и в meta.fields, создаёт при необходимости.
    """
    # Проверяем в meta.fields
    res = db.execute_query("SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname='sourceid'", (entitytype_id,))
    if not res:
        # Создаём поле
        sql = """INSERT INTO meta.fields
                 (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id)
                 VALUES (%s, 'sourceid', %s, 'Source ID', %s, true, 1) RETURNING id"""
        new_id = db.execute_query(sql, (entitytype_id, field_type, length))
        if new_id:
            # Вызываем синхронизацию
            db.execute_procedure("meta.p_field_sync", (new_id[0][0],))
    # Поле уже существует – ничего не делаем


def load_reference_mappings(db: DatabaseService, ref_entitytype_id: int) -> Dict[str, int]:
    """
    Загружает маппинг sourceid -> instanceid для указанной сущности.
    Возвращает словарь {sourceid_value: instanceid}.
    """
    cname = get_entity_cname(db, ref_entitytype_id)
    if not cname:
        return {}
    ext_table = f"ext.ext_{cname}"
    sql = f"""
        SELECT e.sourceid, v.instanceid
        FROM {ext_table} e
        JOIN data.entity_versions v ON v.id = e.versionid
        WHERE e.sourceid IS NOT NULL
    """
    rows = db.execute_query(sql)
    return {str(row[0]): row[1] for row in rows}


def load_source_settings(db: DatabaseService, import_source_id: int) -> Optional['SourceSettings']:
    """
    Загружает настройки из БД в объект SourceSettings.
    """
    from import_models import SourceSettings, Mapping

    # Загружаем основную запись
    sql_src = """SELECT source_type, source_path, format, source_name, id_field
                 FROM meta.import_sources WHERE id = %s"""
    src_row = db.execute_query(sql_src, (import_source_id,))
    if not src_row:
        return None

    source_type, source_path, fmt, source_name, id_field = src_row[0]

    # Загружаем маппинги
    sql_map = """SELECT target_field, source_field, is_reference, ref_entitytypeid, ref_field_name
                 FROM meta.import_mappings
                 WHERE import_source_id = %s
                 ORDER BY id"""
    map_rows = db.execute_query(sql_map, (import_source_id,))

    mappings = []
    for row in map_rows:
        target, source, is_ref, ref_etype, ref_fname = row
        mappings.append(Mapping(
            target_field=target,
            source_field=source,
            is_reference=is_ref,
            ref_entitytype_id=ref_etype,
            ref_field_name=ref_fname
        ))

    return SourceSettings(
        source_type=source_type,
        source_path=source_path,
        format=fmt,
        source_name=source_name,
        id_field=id_field,
        mappings=mappings
    )