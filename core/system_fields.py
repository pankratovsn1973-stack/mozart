# -*- coding: utf-8 -*-
"""
Словарь вшитых полей сущностей Mozart ERP.

Вшитые поля — это поля, которые есть у КАЖДОЙ сущности независимо от её
типа (entitytypeid). Они живут не в ext.ext_<cname>, а в системных таблицах:

  - data.entity_versions     — версии (хроника состояний)
  - data.entity_instances    — экземпляры

В конфигураторе low-code классов (binding_field, display_field и др.)
ссылка на вшитое поле хранится как ОТРИЦАТЕЛЬНЫЙ ID, чтобы не путать
с ID из meta.fields (там ID всегда > 0).

Диапазоны:
  -1  ...  -99    — data.entity_versions
  -100 ... -199   — data.entity_instances

Использование:
    from core.system_fields import SYSTEM_FIELDS, get_system_field

    # Список всех вшитых полей для диалога выбора
    for sid, info in SYSTEM_FIELDS.items():
        print(sid, info["cname"], info["table"], info["calias"])

    # Обратный маппинг
    info = get_system_field(-7)
    # → {"cname": "cname", "table": "data.entity_versions", "calias": "Наименование", ...}
"""

from typing import Optional


# =========================================================================
# data.entity_versions — версии (хроника состояний)
# =========================================================================
ENTITY_VERSION_FIELDS = {
    -1: {
        "cname": "id",
        "table": "data.entity_versions",
        "calias": "ID версии",
        "cfieldtype": "I",
        "comment": "Первичный ключ версии",
    },
    -2: {
        "cname": "instanceid",
        "table": "data.entity_versions",
        "calias": "Экземпляр",
        "cfieldtype": "I",
        "comment": "Ссылка на экземпляр сущности",
    },
    -3: {
        "cname": "parentinstanceid",
        "table": "data.entity_versions",
        "calias": "Родительский экземпляр",
        "cfieldtype": "I",
        "comment": "Ссылка на родителя (для иерархий)",
    },
    -4: {
        "cname": "tdt_start",
        "table": "data.entity_versions",
        "calias": "Начало жизни версии",
        "cfieldtype": "T",
        "comment": "С этого момента данные истинны",
    },
    -5: {
        "cname": "tdt_end",
        "table": "data.entity_versions",
        "calias": "Конец жизни версии",
        "cfieldtype": "T",
        "comment": "9999-12-31 = активная версия",
    },
    -6: {
        "cname": "cversionstatus",
        "table": "data.entity_versions",
        "calias": "Статус версии",
        "cfieldtype": "C",
        "comment": "Active / History / Draft",
    },
    -7: {
        "cname": "cname",
        "table": "data.entity_versions",
        "calias": "Наименование",
        "cfieldtype": "C",
        "comment": "Основное имя объекта на этой версии",
    },
    -8: {
        "cname": "created_by_userid",
        "table": "data.entity_versions",
        "calias": "Создал (пользователь)",
        "cfieldtype": "I",
        "comment": "Аудит",
    },
    -9: {
        "cname": "modified_by_userid",
        "table": "data.entity_versions",
        "calias": "Изменил (пользователь)",
        "cfieldtype": "I",
        "comment": "Аудит",
    },
}


# =========================================================================
# data.entity_instances — экземпляры сущностей
# =========================================================================
ENTITY_INSTANCE_FIELDS = {
    -101: {
        "cname": "id",
        "table": "data.entity_instances",
        "calias": "ID экземпляра",
        "cfieldtype": "I",
        "comment": "Первичный ключ экземпляра",
    },
    -102: {
        "cname": "entitytypeid",
        "table": "data.entity_instances",
        "calias": "Тип сущности",
        "cfieldtype": "I",
        "comment": "Ссылка на meta.entitytypes",
    },
    -103: {
        "cname": "tdt_birth",
        "table": "data.entity_instances",
        "calias": "Дата создания",
        "cfieldtype": "T",
        "comment": "Момент создания экземпляра",
    },
}


# =========================================================================
# Единый словарь
# =========================================================================
SYSTEM_FIELDS = {}
SYSTEM_FIELDS.update(ENTITY_VERSION_FIELDS)
SYSTEM_FIELDS.update(ENTITY_INSTANCE_FIELDS)


# =========================================================================
# Обратный маппинг: cname → отрицательный ID
# =========================================================================
_CNAME_TO_ID = {info["cname"]: sid for sid, info in SYSTEM_FIELDS.items()}


# =========================================================================
# Публичные функции
# =========================================================================
def get_system_field(field_id: int) -> Optional[dict]:
    """Возвращает описание вшитого поля по отрицательному ID."""
    return SYSTEM_FIELDS.get(field_id)


def get_system_field_by_name(cname: str) -> Optional[dict]:
    """Возвращает описание вшитого поля по cname (например, 'cname')."""
    sid = _CNAME_TO_ID.get(cname)
    if sid is None:
        return None
    return SYSTEM_FIELDS[sid]


def is_system_field_id(field_id) -> bool:
    """True, если field_id — отрицательный (вшитое поле)."""
    try:
        return int(field_id) < 0
    except (TypeError, ValueError):
        return False


def list_fields_for_dialog() -> list:
    """
    Возвращает список вшитых полей для диалога выбора:
    [(id, cname, calias, table), ...].
    """
    result = []
    for sid in sorted(SYSTEM_FIELDS.keys()):
        info = SYSTEM_FIELDS[sid]
        result.append((sid, info["cname"], info["calias"], info["table"]))
    return result


def get_sql_expression(field_id: int, version_alias: str = "v") -> Optional[str]:
    """
    Возвращает SQL-выражение для чтения вшитого поля.
    Например, для -7 при alias='v' → 'v.cname'.

    Используется в будущих JOIN'ах в f_build_objpropcol (если понадобится
    подтягивать значения вшитых полей в objpropcol).
    """
    info = get_system_field(field_id)
    if not info:
        return None
    table = info["table"]
    if table == "data.entity_versions":
        return f"{version_alias}.{info['cname']}"
    if table == "data.entity_instances":
        return f"{version_alias}.{info['cname']}"  # через JOIN
    return None