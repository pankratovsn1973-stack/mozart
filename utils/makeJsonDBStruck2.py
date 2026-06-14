#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный дамп структуры PostgreSQL с гибкой настройкой выгрузки.
Управление - только через словари внутри скрипта.
Дополнительно генерирует компактный Markdown-файл для LLM/Aider.
"""

import json
import os
import sys
import psycopg2
from psycopg2 import sql
from datetime import date, datetime, time
from decimal import Decimal

# ======================== ПОДКЛЮЧЕНИЕ К БД ========================
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mozart_erp",
    "user": "postgres",
    "password": "SQLSerIra!"
}

# ======================== НАСТРОЙКИ ВЫГРУЗКИ ========================
DEFAULT_RUNTIME_CONFIG = {
    'output_file': '/home/sergey/Documents/автодок20052026/pg_schema_dump_pr.json',
    'data_limit': 0,  # 0 - все записи, >0 - лимит на таблицу
    'generate_markdown': True,  # Генерировать .md файл для LLM/Aider
    'schemas': {
        'ext': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 1,
            'data': 0,
        },
        'meta': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 1,
        },
        'data': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 0,
        },
        'auth': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 0,
        },
        'autodoc': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 0,
        },
        'lang': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 1,
        },
        'public': {
            'structure': 1,
            'views': 0,
            'routines': 1,
            'indexes': 0,
            'sequences': 0,
            'foreign_keys': 0,
            'comments': 0,
            'data': 0,
        },
    }
}

ALL_SCHEMAS = ['ext', 'meta', 'data', 'auth', 'autodoc', 'lang', 'public']


# ===================================================================


def get_connection(config):
    conn = psycopg2.connect(**config)
    conn.autocommit = True
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


def get_tables_metadata(cursor, schema_name, include_fk, include_comments):
    """Получение метаданных таблиц"""
    tables = []

    try:
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
                # Получаем колонки
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

                    col_data = {
                        "name": col_name,
                        "data_type": data_type,
                        "nullable": not not_null,
                        "default": default,
                        "is_serial": is_serial,
                        "ordinal_position": ordinal
                    }
                    if include_comments:
                        col_data["comment"] = col_comment.strip() if col_comment else None

                    columns.append(col_data)

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

                table_data = {
                    "name": table_name,
                    "columns": columns,
                    "primary_key": primary_key,
                    "unique_constraints": unique_constraints,
                    "check_constraints": check_constraints
                }

                if include_comments and table_comment:
                    table_data["comment"] = table_comment.strip()

                if include_fk:
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
                    table_data["foreign_keys"] = foreign_keys

                tables.append(table_data)

            except Exception as e:
                print(f"    ⚠️ Ошибка обработки таблицы {table_name}: {e}")
                continue

    except Exception as e:
        print(f"    ⚠️ Ошибка получения таблиц: {e}")

    return tables


def get_views_metadata(cursor, schema_name, include_comments):
    """Получение представлений"""
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

                view_data = {
                    "name": view_name,
                    "definition": definition,
                    "columns": columns
                }
                if include_comments and comment:
                    view_data["comment"] = comment.strip()

                views.append(view_data)
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки представления {view_name}: {e}")
                continue

    except Exception as e:
        print(f"    ⚠️ Ошибка получения представлений: {e}")

    return views


def get_routines_metadata(cursor, schema_name, include_comments):
    """Получение процедур, функций и триггеров"""
    routines = []

    try:
        # Процедуры
        cursor.execute("""
            SELECT 
                p.proname,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_functiondef(p.oid) as definition,
                obj_description(p.oid) as comment,
                'procedure' as routine_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s
              AND p.prokind = 'p'
            ORDER BY p.proname
        """, (schema_name,))

        for proc_name, arguments, definition, comment, routine_type in cursor.fetchall():
            routine_data = {
                "name": proc_name,
                "arguments": arguments,
                "definition": definition,
                "type": routine_type
            }
            if include_comments and comment:
                routine_data["comment"] = comment.strip()
            routines.append(routine_data)

        # Функции
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
                END as routine_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s
              AND p.prokind IN ('f', 'w', 'a')
            ORDER BY p.proname
        """, (schema_name,))

        for func_name, arguments, result_type, definition, comment, routine_type in cursor.fetchall():
            routine_data = {
                "name": func_name,
                "arguments": arguments,
                "result_type": result_type if result_type else "void",
                "definition": definition,
                "type": routine_type
            }
            if include_comments and comment:
                routine_data["comment"] = comment.strip()
            routines.append(routine_data)

        # Триггеры
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

            trigger_data = {
                "name": trigger_name,
                "table": f"{schema_name}.{table_name}",
                "definition": definition,
                "level": level,
                "timing": timing,
                "events": events,
                "type": "trigger"
            }
            if include_comments and comment:
                trigger_data["comment"] = comment.strip()
            routines.append(trigger_data)

    except Exception as e:
        print(f"    ⚠️ Ошибка получения процедур/функций/триггеров: {e}")

    return routines


def get_indexes_metadata(cursor, schema_name, include_comments):
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
            index_data = {
                "name": index_name,
                "table": f"{schema_name}.{table_name}",
                "definition": definition,
                "is_unique": is_unique,
                "is_primary": is_primary,
                "method": method
            }
            if include_comments and comment:
                index_data["comment"] = comment.strip()
            indexes.append(index_data)
    except Exception as e:
        print(f"    ⚠️ Ошибка получения индексов: {e}")

    return indexes


def get_sequences_metadata(cursor, schema_name, include_comments):
    """Получение последовательностей"""
    sequences = []

    try:
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

                seq_data = {
                    "name": seq_name,
                    "start_value": seq_params[0] if seq_params else 1,
                    "minimum_value": seq_params[1] if seq_params else 1,
                    "maximum_value": seq_params[2] if seq_params else 9223372036854775807,
                    "increment": seq_params[3] if seq_params else 1
                }
                if include_comments and comment:
                    seq_data["comment"] = comment.strip()
                sequences.append(seq_data)
            except Exception as e:
                print(f"    ⚠️ Ошибка получения параметров последовательности {seq_name}: {e}")
                seq_data = {
                    "name": seq_name,
                    "start_value": 1,
                    "minimum_value": 1,
                    "maximum_value": 9223372036854775807,
                    "increment": 1
                }
                if include_comments and comment:
                    seq_data["comment"] = comment.strip()
                sequences.append(seq_data)

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


def generate_markdown(result, md_file_path):
    """
    Генерирует компактный Markdown-файл с описанием структуры БД для LLM/Aider.
    Использует данные из result["schemas"].
    """
    print(f"\nГенерация Markdown-файла: {md_file_path}")
    try:
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write("# Дамп структуры базы данных\n\n")
            export_info = result.get("export_info", {})
            f.write(f"- **База данных:** {export_info.get('database', 'N/A')}\n")
            f.write(f"- **Хост:** {export_info.get('host', 'N/A')}\n")
            f.write(f"- **Дата экспорта:** {export_info.get('export_timestamp', 'N/A')}\n")
            f.write(f"- **Схемы:** {', '.join(export_info.get('schemas_processed', []))}\n\n")

            for schema_name, schema_data in result.get("schemas", {}).items():
                f.write(f"## Схема `{schema_name}`\n")
                if schema_data.get("comment"):
                    f.write(f"\n*Комментарий:* {schema_data['comment']}\n")

                # Таблицы
                if "tables" in schema_data and schema_data["tables"]:
                    f.write("\n### Таблицы\n")
                    for table in schema_data["tables"]:
                        f.write(f"\n#### `{table['name']}`\n")
                        if table.get("comment"):
                            f.write(f"\n*Комментарий:* {table['comment']}\n")

                        # Колонки
                        f.write("\n**Колонки:**\n")
                        f.write("| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |\n")
                        f.write("|-----|-----|----------|--------------|--------|-------------|\n")
                        for col in table["columns"]:
                            serial_flag = "✅" if col.get("is_serial") else ""
                            default_val = col.get("default", "")
                            if default_val is None:
                                default_val = ""
                            comment = col.get("comment", "")
                            f.write(f"| {col['name']} | {col['data_type']} | "
                                    f"{'❌' if not col['nullable'] else '✅'} | "
                                    f"{default_val} | {serial_flag} | {comment} |\n")

                        # Первичный ключ
                        if table.get("primary_key"):
                            f.write(f"\n**Первичный ключ:** `{', '.join(table['primary_key'])}`\n")

                        # Уникальные ограничения
                        if table.get("unique_constraints"):
                            f.write("\n**Уникальные ограничения:**\n")
                            for const_name, cols in table["unique_constraints"].items():
                                f.write(f"- `{const_name}`: (`{', '.join(cols)}`)\n")

                        # Check-ограничения
                        if table.get("check_constraints"):
                            f.write("\n**Check-ограничения:**\n")
                            for cc in table["check_constraints"]:
                                f.write(f"- `{cc['name']}`: {cc['definition']}\n")

                        # Внешние ключи
                        if table.get("foreign_keys"):
                            f.write("\n**Внешние ключи:**\n")
                            for fk in table["foreign_keys"]:
                                f.write(f"- `{fk['column']}` → `{fk['ref_schema']}.{fk['ref_table']}.{fk['ref_column']}` "
                                        f"(constraint: {fk['constraint_name']})\n")
                        f.write("\n---\n")

                # Представления
                if "views" in schema_data and schema_data["views"]:
                    f.write("\n### Представления\n")
                    for view in schema_data["views"]:
                        f.write(f"\n#### `{view['name']}`\n")
                        if view.get("comment"):
                            f.write(f"\n*Комментарий:* {view['comment']}\n")
                        f.write("\n**Колонки:**\n")
                        for col in view.get("columns", []):
                            f.write(f"- `{col['name']}` : {col['data_type']}\n")
                        f.write("\n**Определение:**\n```sql\n")
                        f.write(view.get("definition", ""))
                        f.write("\n```\n---\n")

                # Процедуры/функции/триггеры
                if "routines" in schema_data and schema_data["routines"]:
                    f.write("\n### Хранимые процедуры, функции и триггеры\n")
                    for routine in schema_data["routines"]:
                        rtype = routine.get("type", "unknown")
                        if rtype == "trigger":
                            f.write(f"\n#### Триггер `{routine['name']}`\n")
                            f.write(f"- **Таблица:** `{routine.get('table', 'N/A')}`\n")
                            f.write(f"- **Уровень:** {routine.get('level', 'N/A')}\n")
                            f.write(f"- **Время:** {routine.get('timing', 'N/A')}\n")
                            f.write(f"- **События:** {', '.join(routine.get('events', []))}\n")
                            if routine.get("comment"):
                                f.write(f"- **Комментарий:** {routine['comment']}\n")
                            f.write("\n**Определение:**\n```sql\n")
                            f.write(routine.get("definition", ""))
                            f.write("\n```\n")
                        else:
                            f.write(f"\n#### {rtype.capitalize()} `{routine['name']}`\n")
                            if rtype in ("function", "window_function", "aggregate_function"):
                                f.write(f"- **Сигнатура:** `{routine['name']}({routine.get('arguments', '')})`\n")
                                f.write(f"- **Возвращает:** {routine.get('result_type', 'void')}\n")
                            else:  # procedure
                                f.write(f"- **Параметры:** `{routine.get('arguments', '')}`\n")
                            if routine.get("comment"):
                                f.write(f"- **Комментарий:** {routine['comment']}\n")
                            f.write("\n**Определение:**\n```sql\n")
                            f.write(routine.get("definition", ""))
                            f.write("\n```\n")
                        f.write("---\n")

        print(f"✅ Markdown-файл успешно создан: {md_file_path}")
    except Exception as e:
        print(f"❌ Ошибка генерации Markdown: {e}")


def main():
    print("=" * 60)
    print("ЗАПУСК ЭКСПОРТА СТРУКТУРЫ И ДАННЫХ POSTGRESQL")
    print("=" * 60)

    # Загружаем настройки
    config = DEFAULT_RUNTIME_CONFIG
    output_file = config['output_file']
    data_limit = config['data_limit']
    schemas_config = config['schemas']
    generate_md = config.get('generate_markdown', True)

    # Проверяем, что все схемы из ALL_SCHEMAS описаны
    missing_schemas = set(ALL_SCHEMAS) - set(schemas_config.keys())
    if missing_schemas:
        print(f"❌ Ошибка: не все схемы описаны в конфигурации. Отсутствуют: {missing_schemas}")
        sys.exit(1)

    print(f"Файл выгрузки: {output_file}")
    print(f"Лимит записей на таблицу: {data_limit if data_limit > 0 else 'без лимита'}")
    print("\nНастройки выгрузки по схемам:")
    for schema in ALL_SCHEMAS:
        cfg = schemas_config[schema]
        print(f"  {schema}: структура={cfg['structure']}, представления={cfg['views']}, "
              f"проц/функ/триг={cfg['routines']}, индексы={cfg['indexes']}, "
              f"последоват={cfg['sequences']}, внеш.ключи={cfg['foreign_keys']}, "
              f"комментарии={cfg['comments']}, данные={cfg['data']}")

    try:
        conn = get_connection(DEFAULT_DB_CONFIG)
        cursor = conn.cursor()
        print(f"\n✅ Подключено к {DEFAULT_DB_CONFIG['host']}:{DEFAULT_DB_CONFIG['port']}/{DEFAULT_DB_CONFIG['dbname']}")

        result = {
            "export_info": {
                "database": DEFAULT_DB_CONFIG["dbname"],
                "host": DEFAULT_DB_CONFIG["host"],
                "export_timestamp": datetime.now().isoformat(),
                "schemas_processed": ALL_SCHEMAS
            },
            "schemas": {}
        }

        for schema in ALL_SCHEMAS:
            print(f"\n{'=' * 60}")
            print(f"ОБРАБОТКА СХЕМЫ: {schema}")
            print(f"{'=' * 60}")

            cfg = schemas_config[schema]

            schema_data = {
                "schema_name": schema,
            }

            # Комментарий схемы
            if cfg['comments']:
                schema_data["comment"] = get_schema_comment(cursor, schema)

            # Структура (таблицы)
            if cfg['structure']:
                print("  Таблицы...")
                schema_data["tables"] = get_tables_metadata(
                    cursor, schema,
                    include_fk=cfg['foreign_keys'],
                    include_comments=cfg['comments']
                )
                print(f"    Таблиц: {len(schema_data.get('tables', []))}")

            # Представления
            if cfg['views']:
                print("  Представления...")
                schema_data["views"] = get_views_metadata(cursor, schema, cfg['comments'])
                print(f"    Представлений: {len(schema_data.get('views', []))}")

            # Процедуры, функции, триггеры
            if cfg['routines']:
                print("  Процедуры, функции, триггеры...")
                schema_data["routines"] = get_routines_metadata(cursor, schema, cfg['comments'])
                print(f"    Объектов: {len(schema_data.get('routines', []))}")

            # Индексы
            if cfg['indexes']:
                print("  Индексы...")
                schema_data["indexes"] = get_indexes_metadata(cursor, schema, cfg['comments'])
                print(f"    Индексов: {len(schema_data.get('indexes', []))}")

            # Последовательности
            if cfg['sequences']:
                print("  Последовательности...")
                schema_data["sequences"] = get_sequences_metadata(cursor, schema, cfg['comments'])
                print(f"    Последовательностей: {len(schema_data.get('sequences', []))}")

            # Данные
            if cfg['data'] and cfg['structure']:
                print("  Выгрузка данных из таблиц...")
                schema_data["table_data"] = {}
                for table in schema_data.get("tables", []):
                    table_name = table["name"]
                    print(f"    {schema}.{table_name}")
                    rows = get_table_data(cursor, schema, table_name, limit=data_limit)
                    if rows:
                        schema_data["table_data"][table_name] = rows
                        print(f"      Записей: {len(rows)}")
                    else:
                        print(f"      Записей: 0")

            result["schemas"][schema] = schema_data

        # Сохраняем результат в JSON
        print(f"\n{'=' * 60}")
        print("СОХРАНЕНИЕ JSON-РЕЗУЛЬТАТА...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=json_serializer)

        # Генерируем Markdown, если требуется
        if generate_md:
            md_file = os.path.splitext(output_file)[0] + ".md"
            generate_markdown(result, md_file)

        # Статистика
        print(f"\n{'=' * 60}")
        print("СТАТИСТИКА ЭКСПОРТА")
        print(f"{'=' * 60}")

        for schema in ALL_SCHEMAS:
            schema_result = result["schemas"][schema]
            stats = []
            if "tables" in schema_result:
                stats.append(f"таблиц={len(schema_result['tables'])}")
            if "views" in schema_result:
                stats.append(f"предст={len(schema_result['views'])}")
            if "routines" in schema_result:
                stats.append(f"рутин={len(schema_result['routines'])}")
            if "indexes" in schema_result:
                stats.append(f"индексов={len(schema_result['indexes'])}")
            if "sequences" in schema_result:
                stats.append(f"послед={len(schema_result['sequences'])}")
            if "table_data" in schema_result:
                tables_with_data = len(schema_result['table_data'])
                stats.append(f"таблиц с данными={tables_with_data}")
            print(f"  {schema}: {', '.join(stats)}")

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size > 1024 * 1024:
                print(f"\nРазмер JSON-файла: {file_size / (1024 * 1024):.2f} MB")
            else:
                print(f"\nРазмер JSON-файла: {file_size / 1024:.2f} KB")

        if generate_md and os.path.exists(md_file):
            md_size = os.path.getsize(md_file)
            if md_size > 1024 * 1024:
                print(f"Размер MD-файла: {md_size / (1024 * 1024):.2f} MB")
            else:
                print(f"Размер MD-файла: {md_size / 1024:.2f} KB")

        cursor.close()
        conn.close()
        print("\n✅ ЭКСПОРТ УСПЕШНО ЗАВЕРШЁН!")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()