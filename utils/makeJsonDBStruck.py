#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
самостоятельное получение дстрктуры с серверау
Расширенный дамп структуры PostgreSQL и выборочно данных.
Работает как из командной строки, так и из IDE (задать параметры в секции DEFAULT_RUNTIME_CONFIG).
"""
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправленный дамп структуры PostgreSQL с полными комментариями, 
процедурами, функциями, триггерами и данными.
"""

import json
import sys
import argparse
import os
import psycopg2
from psycopg2 import sql
from datetime import date, datetime, time
from decimal import Decimal

# ======================== НАСТРОЙКИ ПО УМОЛЧАНИЮ ========================
DEFAULT_RUNTIME_CONFIG = {
    'all': -1,  # -1: только структура, 0: выборочные данные, 1: все данные
    'schemas': {  # 1 - обрабатывать, 0 - пропустить
        'ext': 1,
        'meta': 1,
        'data': 1,
        'auth': 1,
        'autodoc': 1,
        'lang': 1,
        'public': 1,
    },
    'data_limit': 0,  # 0 - без ограничений, >0 - лимит записей на таблицу
    'output_file': 'pg_schema_dump_full.json'
}
# ========================================================================

ALL_SCHEMAS = ['ext', 'meta', 'data', 'auth', 'autodoc', 'lang', 'public']

DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mozart_erp",
    "user": "postgres",
    "password": "SQLSerIra!"
}


def get_connection(config):
    conn = psycopg2.connect(**config)
    conn.autocommit = True  # Включаем autocommit чтобы ошибки не ломали транзакцию
    return conn


def json_serializer(obj):
    """Сериализатор для типов, не поддерживаемых JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def get_schema_comment(cursor, schema_name):
    """Получение комментария к схеме"""
    try:
        cursor.execute("""
            SELECT obj_description(n.oid, 'pg_namespace')
            FROM pg_namespace n
            WHERE n.nspname = %s
        """, (schema_name,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else None
    except Exception as e:
        print(f"    ⚠️ Ошибка получения комментария схемы: {e}")
        return None


def get_tables_metadata(cursor, schema_name):
    """Получение полных метаданных таблиц с комментариями"""
    tables = []

    try:
        # Получаем все таблицы схемы
        cursor.execute("""
            SELECT c.relname as table_name,
                   obj_description(c.oid) as table_comment
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s 
              AND c.relkind = 'r'
            ORDER BY c.relname
        """, (schema_name,))

        table_rows = cursor.fetchall()

        for table_name, table_comment in table_rows:
            try:
                # Получаем колонки с комментариями
                cursor.execute("""
                    SELECT 
                        a.attname as column_name,
                        pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                        a.attnotnull as not_null,
                        pg_get_expr(d.adbin, d.adrelid) as column_default,
                        col_description(c.oid, a.attnum) as column_comment,
                        a.attnum as ordinal_position
                    FROM pg_catalog.pg_attribute a
                    LEFT JOIN pg_catalog.pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
                    JOIN pg_class c ON a.attrelid = c.oid
                    WHERE c.relname = %s
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                      AND a.attnum > 0 
                      AND NOT a.attisdropped
                    ORDER BY a.attnum
                """, (table_name, schema_name))

                columns = []
                for col in cursor.fetchall():
                    col_name, data_type, not_null, default, col_comment, ordinal = col
                    is_serial = default is not None and 'nextval' in str(default)

                    columns.append({
                        "name": col_name,
                        "data_type": data_type,
                        "nullable": not not_null,
                        "default": default,
                        "is_serial": is_serial,
                        "comment": col_comment.strip() if col_comment else None,
                        "ordinal_position": ordinal
                    })

                # Получаем первичный ключ
                cursor.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass 
                      AND i.indisprimary
                    ORDER BY array_position(i.indkey, a.attnum)
                """, (f"{schema_name}.{table_name}",))
                primary_key = [row[0] for row in cursor.fetchall()]

                # Получаем внешние ключи
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_schema AS ref_schema,
                        ccu.table_name AS ref_table,
                        ccu.column_name AS ref_column,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = %s
                      AND tc.table_name = %s
                    ORDER BY kcu.ordinal_position
                """, (schema_name, table_name))

                foreign_keys = []
                for fk in cursor.fetchall():
                    foreign_keys.append({
                        "column": fk[0],
                        "ref_schema": fk[1],
                        "ref_table": fk[2],
                        "ref_column": fk[3],
                        "constraint_name": fk[4]
                    })

                # Получаем уникальные ограничения
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'UNIQUE'
                      AND tc.table_schema = %s
                      AND tc.table_name = %s
                    ORDER BY tc.constraint_name, kcu.ordinal_position
                """, (schema_name, table_name))

                unique_constraints = {}
                for uc in cursor.fetchall():
                    const_name, col_name = uc
                    if const_name not in unique_constraints:
                        unique_constraints[const_name] = []
                    unique_constraints[const_name].append(col_name)

                # Получаем check-ограничения
                cursor.execute("""
                    SELECT
                        conname,
                        pg_get_constraintdef(oid) as definition
                    FROM pg_constraint
                    WHERE conrelid = %s::regclass
                      AND contype = 'c'
                    ORDER BY conname
                """, (f"{schema_name}.{table_name}",))

                check_constraints = []
                for cc in cursor.fetchall():
                    check_constraints.append({
                        "name": cc[0],
                        "definition": cc[1]
                    })

                tables.append({
                    "name": table_name,
                    "comment": table_comment.strip() if table_comment else None,
                    "columns": columns,
                    "primary_key": primary_key,
                    "foreign_keys": foreign_keys,
                    "unique_constraints": unique_constraints,
                    "check_constraints": check_constraints
                })
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки таблицы {table_name}: {e}")
                continue

    except Exception as e:
        print(f"    ⚠️ Ошибка получения таблиц: {e}")

    return tables


def get_views_metadata(cursor, schema_name):
    """Получение представлений с комментариями"""
    views = []

    try:
        cursor.execute("""
            SELECT 
                c.relname as view_name,
                pg_get_viewdef(c.oid) as definition,
                obj_description(c.oid) as comment
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s
              AND c.relkind = 'v'
            ORDER BY c.relname
        """, (schema_name,))

        for view_name, definition, comment in cursor.fetchall():
            try:
                cursor.execute("""
                    SELECT 
                        a.attname as column_name,
                        pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type
                    FROM pg_catalog.pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    WHERE c.relname = %s
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                    ORDER BY a.attnum
                """, (view_name, schema_name))

                columns = [{"name": col[0], "data_type": col[1]} for col in cursor.fetchall()]

                views.append({
                    "name": view_name,
                    "definition": definition,
                    "columns": columns,
                    "comment": comment.strip() if comment else None
                })
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки представления {view_name}: {e}")
                continue

    except Exception as e:
        print(f"    ⚠️ Ошибка получения представлений: {e}")

    return views


def get_procedures_metadata(cursor, schema_name):
    """Получение хранимых процедур"""
    procedures = []

    try:
        cursor.execute("""
            SELECT 
                p.proname,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_functiondef(p.oid) as definition,
                obj_description(p.oid) as comment
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s
              AND p.prokind = 'p'
            ORDER BY p.proname
        """, (schema_name,))

        for proc_name, arguments, definition, comment in cursor.fetchall():
            procedures.append({
                "name": proc_name,
                "arguments": arguments,
                "definition": definition,
                "comment": comment.strip() if comment else None,
                "type": "procedure"
            })
    except Exception as e:
        print(f"    ⚠️ Ошибка получения процедур: {e}")

    return procedures


def get_functions_metadata(cursor, schema_name):
    """Получение функций"""
    functions = []

    try:
        cursor.execute("""
            SELECT 
                p.proname,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as result_type,
                pg_get_functiondef(p.oid) as definition,
                obj_description(p.oid) as comment,
                CASE p.prokind
                    WHEN 'f' THEN 'function'
                    WHEN 'w' THEN 'window_function'
                    WHEN 'a' THEN 'aggregate_function'
                END as func_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s
              AND p.prokind IN ('f', 'w', 'a')
            ORDER BY p.proname
        """, (schema_name,))

        for func_name, arguments, result_type, definition, comment, func_type in cursor.fetchall():
            functions.append({
                "name": func_name,
                "arguments": arguments,
                "result_type": result_type if result_type else "void",
                "definition": definition,
                "comment": comment.strip() if comment else None,
                "type": func_type
            })
    except Exception as e:
        print(f"    ⚠️ Ошибка получения функций: {e}")

    return functions


def get_triggers_metadata(cursor, schema_name):
    """Получение триггеров"""
    triggers = []

    try:
        cursor.execute("""
            SELECT 
                t.tgname,
                c.relname as table_name,
                pg_get_triggerdef(t.oid) as definition,
                obj_description(t.oid) as comment,
                CASE 
                    WHEN t.tgtype & 1 = 1 THEN 'ROW' 
                    ELSE 'STATEMENT' 
                END as trigger_level,
                CASE 
                    WHEN t.tgtype & 2 = 2 THEN 'BEFORE' 
                    WHEN t.tgtype & 4 = 4 THEN 'AFTER'
                    WHEN t.tgtype & 64 = 64 THEN 'INSTEAD OF'
                END as trigger_timing,
                t.tgtype
            FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s
              AND NOT t.tgisinternal
            ORDER BY c.relname, t.tgname
        """, (schema_name,))

        for trigger_name, table_name, definition, comment, level, timing, tgtype in cursor.fetchall():
            events = []
            if tgtype & 4:
                events.append('INSERT')
            if tgtype & 8:
                events.append('DELETE')
            if tgtype & 16:
                events.append('UPDATE')
            if tgtype & 32:
                events.append('TRUNCATE')

            triggers.append({
                "name": trigger_name,
                "table": f"{schema_name}.{table_name}",
                "definition": definition,
                "comment": comment.strip() if comment else None,
                "level": level,
                "timing": timing,
                "events": events
            })
    except Exception as e:
        print(f"    ⚠️ Ошибка получения триггеров: {e}")

    return triggers


def get_indexes_metadata(cursor, schema_name):
    """Получение индексов"""
    indexes = []

    try:
        cursor.execute("""
            SELECT 
                i.relname as index_name,
                c.relname as table_name,
                pg_get_indexdef(i.oid) as definition,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary,
                am.amname as index_method,
                obj_description(i.oid) as comment
            FROM pg_index idx
            JOIN pg_class i ON idx.indexrelid = i.oid
            JOIN pg_class c ON idx.indrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_am am ON i.relam = am.oid
            WHERE n.nspname = %s
              AND NOT idx.indisprimary
            ORDER BY c.relname, i.relname
        """, (schema_name,))

        for index_name, table_name, definition, is_unique, is_primary, method, comment in cursor.fetchall():
            indexes.append({
                "name": index_name,
                "table": f"{schema_name}.{table_name}",
                "definition": definition,
                "is_unique": is_unique,
                "is_primary": is_primary,
                "method": method,
                "comment": comment.strip() if comment else None
            })
    except Exception as e:
        print(f"    ⚠️ Ошибка получения индексов: {e}")

    return indexes


def get_sequences_metadata(cursor, schema_name):
    """Получение последовательностей"""
    sequences = []

    try:
        # Получаем список последовательностей из pg_class
        cursor.execute("""
            SELECT 
                c.relname as sequence_name,
                obj_description(c.oid) as comment
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s
              AND c.relkind = 'S'
            ORDER BY c.relname
        """, (schema_name,))

        seq_list = cursor.fetchall()

        for seq_name, comment in seq_list:
            try:
                # Получаем параметры через отдельный запрос с pg_sequence (без 's')
                cursor.execute("""
                    SELECT 
                        seqstart,
                        seqmin,
                        seqmax,
                        seqincrement
                    FROM pg_sequence s
                    JOIN pg_class c ON s.seqrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s AND c.relname = %s
                """, (schema_name, seq_name))

                seq_params = cursor.fetchone()

                if seq_params:
                    sequences.append({
                        "name": seq_name,
                        "start_value": seq_params[0],
                        "minimum_value": seq_params[1],
                        "maximum_value": seq_params[2],
                        "increment": seq_params[3],
                        "comment": comment.strip() if comment else None
                    })
                else:
                    # Если не удалось получить параметры, добавляем с базовой информацией
                    sequences.append({
                        "name": seq_name,
                        "start_value": 1,
                        "minimum_value": 1,
                        "maximum_value": 9223372036854775807,
                        "increment": 1,
                        "comment": comment.strip() if comment else None
                    })
            except Exception as e:
                print(f"    ⚠️ Ошибка получения параметров последовательности {seq_name}: {e}")
                # Добавляем с базовой информацией
                sequences.append({
                    "name": seq_name,
                    "start_value": 1,
                    "minimum_value": 1,
                    "maximum_value": 9223372036854775807,
                    "increment": 1,
                    "comment": comment.strip() if comment else None
                })

    except Exception as e:
        print(f"    ⚠️ Ошибка получения списка последовательностей: {e}")

    return sequences


def get_table_data(cursor, schema_name, table_name, limit=0):
    """Получение данных таблицы"""
    try:
        if limit > 0:
            cursor.execute(
                sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                ), (limit,)
            )
        else:
            cursor.execute(
                sql.SQL("SELECT * FROM {}.{}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )
            )

        rows = cursor.fetchall()
        if not rows:
            return []

        columns = [desc[0] for desc in cursor.description]
        result = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                if isinstance(val, (datetime, date, time)):
                    val = val.isoformat()
                elif isinstance(val, Decimal):
                    val = float(val)
                elif isinstance(val, bytes):
                    val = val.decode('utf-8', errors='replace')
                row_dict[col] = val
            result.append(row_dict)
        return result
    except Exception as e:
        print(f"      Ошибка выгрузки данных из {schema_name}.{table_name}: {e}")
        return []


def get_schema_overview(cursor):
    """Получение общей информации о схемах"""
    overview = []

    try:
        cursor.execute("""
            SELECT 
                n.nspname,
                obj_description(n.oid, 'pg_namespace') as comment,
                (SELECT COUNT(*) FROM pg_class c WHERE c.relnamespace = n.oid AND c.relkind = 'r') as table_count,
                (SELECT COUNT(*) FROM pg_class c WHERE c.relnamespace = n.oid AND c.relkind = 'v') as view_count,
                (SELECT COUNT(*) FROM pg_proc p WHERE p.pronamespace = n.oid AND p.prokind = 'p') as procedure_count,
                (SELECT COUNT(*) FROM pg_proc p WHERE p.pronamespace = n.oid AND p.prokind IN ('f', 'w', 'a')) as function_count
            FROM pg_namespace n
            WHERE n.nspname IN ('ext', 'meta', 'data', 'auth', 'autodoc', 'lang', 'public')
            ORDER BY n.nspname
        """)

        for schema_name, comment, tbl_count, view_count, proc_count, func_count in cursor.fetchall():
            overview.append({
                "schema_name": schema_name,
                "comment": comment,
                "table_count": tbl_count,
                "view_count": view_count,
                "procedure_count": proc_count,
                "function_count": func_count
            })
    except Exception as e:
        print(f"⚠️ Ошибка получения обзора схем: {e}")

    return overview


def main():
    if len(sys.argv) == 1:
        print("Запуск без аргументов. Использую настройки из DEFAULT_RUNTIME_CONFIG.")
        all_mode = DEFAULT_RUNTIME_CONFIG['all']
        schemas_config = DEFAULT_RUNTIME_CONFIG['schemas']
        data_limit = DEFAULT_RUNTIME_CONFIG['data_limit']
        output_file = DEFAULT_RUNTIME_CONFIG['output_file']
        config_file = None
    else:
        parser = argparse.ArgumentParser(description='Полный дамп структуры PostgreSQL')
        parser.add_argument('config_file', nargs='?', help='JSON файл с параметрами подключения')
        parser.add_argument('-all', type=int, choices=[-1, 0, 1], default=0,
                            help='-1: структура, 0: выборочные данные, 1: все данные')
        for schema in ALL_SCHEMAS:
            parser.add_argument(f'-{schema}', type=int, choices=[0, 1], default=1,
                                help=f'Обрабатывать схему {schema} (1) или нет (0)')
        parser.add_argument('-limit', type=int, default=0,
                            help='Лимит записей на таблицу (0 - все)')
        parser.add_argument('-output', default='pg_schema_dump_full.json',
                            help='Имя выходного файла')
        args = parser.parse_args()

        all_mode = args.all
        schemas_config = {}
        for schema in ALL_SCHEMAS:
            schemas_config[schema] = getattr(args, schema, 1)
        data_limit = args.limit
        output_file = args.output
        config_file = args.config_file

    # Загрузка конфигурации подключения
    if config_file:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        db_cfg = config_data.get("db", {})
        db_config = {
            "host": db_cfg.get("host", DEFAULT_DB_CONFIG["host"]),
            "port": int(db_cfg.get("port", DEFAULT_DB_CONFIG["port"])),
            "dbname": db_cfg.get("name", DEFAULT_DB_CONFIG["dbname"]),
            "user": db_cfg.get("user", DEFAULT_DB_CONFIG["user"]),
            "password": db_cfg.get("pass", DEFAULT_DB_CONFIG["password"])
        }
    else:
        db_config = DEFAULT_DB_CONFIG

    # Определяем схемы для обработки
    schemas_to_process = [s for s in ALL_SCHEMAS if schemas_config.get(s, 0) == 1]

    # Определяем для каких схем выгружать данные
    schemas_to_load_data = set()
    if all_mode != -1:
        if all_mode == 1:
            schemas_to_load_data = set(schemas_to_process)
        else:
            schemas_to_load_data = set(schemas_to_process) - {'data', 'ext'}

    print(f"Будет обработано схем: {len(schemas_to_process)}")
    print(f"Схемы: {', '.join(schemas_to_process)}")
    print(f"Данные будут выгружены для схем: {', '.join(schemas_to_load_data) if schemas_to_load_data else 'нет'}")
    if data_limit > 0:
        print(f"Лимит записей на таблицу: {data_limit}")

    try:
        conn = get_connection(db_config)
        cursor = conn.cursor()

        result = {
            "export_info": {
                "database": db_config["dbname"],
                "host": db_config["host"],
                "export_timestamp": datetime.now().isoformat(),
                "total_schemas": len(schemas_to_process),
                "schemas_list": schemas_to_process
            },
            "schema_overview": get_schema_overview(cursor),
            "schemas": {}
        }

        for schema in schemas_to_process:
            print(f"\n{'=' * 60}")
            print(f"Обработка схемы: {schema}")
            print(f"{'=' * 60}")

            schema_data = {
                "schema_name": schema,
                "comment": get_schema_comment(cursor, schema),
                "tables": [],
                "views": [],
                "procedures": [],
                "functions": [],
                "triggers": [],
                "indexes": [],
                "sequences": [],
                "table_data": {}
            }

            # Получаем метаданные с обработкой ошибок
            print("  Получение таблиц...")
            schema_data["tables"] = get_tables_metadata(cursor, schema)
            print(f"    Найдено таблиц: {len(schema_data['tables'])}")

            print("  Получение представлений...")
            schema_data["views"] = get_views_metadata(cursor, schema)
            print(f"    Найдено представлений: {len(schema_data['views'])}")

            print("  Получение процедур...")
            schema_data["procedures"] = get_procedures_metadata(cursor, schema)
            print(f"    Найдено процедур: {len(schema_data['procedures'])}")

            print("  Получение функций...")
            schema_data["functions"] = get_functions_metadata(cursor, schema)
            print(f"    Найдено функций: {len(schema_data['functions'])}")

            print("  Получение триггеров...")
            schema_data["triggers"] = get_triggers_metadata(cursor, schema)
            print(f"    Найдено триггеров: {len(schema_data['triggers'])}")

            print("  Получение индексов...")
            schema_data["indexes"] = get_indexes_metadata(cursor, schema)
            print(f"    Найдено индексов: {len(schema_data['indexes'])}")

            print("  Получение последовательностей...")
            schema_data["sequences"] = get_sequences_metadata(cursor, schema)
            print(f"    Найдено последовательностей: {len(schema_data['sequences'])}")

            # Выгружаем данные если нужно
            if schema in schemas_to_load_data:
                print(f"  Выгрузка данных...")
                for table in schema_data["tables"]:
                    table_name = table["name"]
                    print(f"    Таблица: {schema}.{table_name}")
                    rows = get_table_data(cursor, schema, table_name, limit=data_limit)
                    if rows:
                        schema_data["table_data"][table_name] = rows
                        print(f"      Записей: {len(rows)}")

            result["schemas"][schema] = schema_data

        # Сохраняем результат
        print(f"\n{'=' * 60}")
        print("Сохранение результата...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=json_serializer)

        # Статистика
        total_tables = sum(len(s["tables"]) for s in result["schemas"].values())
        total_views = sum(len(s["views"]) for s in result["schemas"].values())
        total_procedures = sum(len(s["procedures"]) for s in result["schemas"].values())
        total_functions = sum(len(s["functions"]) for s in result["schemas"].values())
        total_triggers = sum(len(s["triggers"]) for s in result["schemas"].values())

        print(f"\n{'=' * 60}")
        print("СТАТИСТИКА ЭКСПОРТА")
        print(f"{'=' * 60}")
        print(f"Схем:           {len(result['schemas'])}")
        print(f"Таблиц:         {total_tables}")
        print(f"Представлений:  {total_views}")
        print(f"Процедур:       {total_procedures}")
        print(f"Функций:        {total_functions}")
        print(f"Триггеров:      {total_triggers}")
        print(f"\nФайл: {output_file}")

        # Размер файла
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size > 1024 * 1024:
                print(f"Размер: {file_size / (1024 * 1024):.2f} MB")
            else:
                print(f"Размер: {file_size / 1024:.2f} KB")

        cursor.close()
        conn.close()
        print("\n✅ Экспорт успешно завершен!")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()