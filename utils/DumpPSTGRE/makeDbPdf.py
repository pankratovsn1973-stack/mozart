#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Выгружает структуру (и выборочно данные) PostgreSQL в PDF.
Настройки – в секции CONFIG в начале скрипта.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2 import sql
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ======================== КОНФИГУРАЦИЯ (редактируйте здесь) ========================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mozart_erp",
    "user": "postgres",
    "password": "SQLSerIra"
}

ALL = -1   # -1: только структура, 0: данные из meta/auth/autodoc/lang/public (кроме data/ext), 1: все данные
SCHEMAS_CONFIG = {
    'ext': None,       # None – обрабатывать (по умолчанию), 0 – пропустить, 1 – принудительно
    'meta': None,
    'data': None,
    'auth': None,
    'autodoc': None,
    'lang': None,
    'public': None,
}
EXTRA_DATA_TABLES = []   # список строк 'schema.table' для принудительной выгрузки данных (даже если ALL=-1)
DATA_LIMIT = 10          # максимум строк данных на таблицу
OUTPUT_FILE = "../db_structure.pdf"

# Шрифт с кириллицей (если не найден – будет Helvetica)
CYRILLIC_FONT = None
for font_path in [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
            CYRILLIC_FONT = 'CyrillicFont'
            break
        except:
            pass
if not CYRILLIC_FONT:
    print("Предупреждение: шрифт с кириллицей не найден, используется Helvetica (латиница).")
    CYRILLIC_FONT = 'Helvetica'
# =================================================================================

ALL_SCHEMAS = ['ext', 'meta', 'data', 'auth', 'autodoc', 'lang', 'public']

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def json_serializer(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def safe_fetch(cursor, query, params=None):
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        print(f"    Ошибка запроса: {e}")
        return []

def get_schema_comment(cursor, schema_name):
    rows = safe_fetch(cursor, "SELECT obj_description(oid) FROM pg_namespace WHERE nspname = %s", (schema_name,))
    return rows[0][0] if rows else None

def get_tables_metadata(cursor, schema_name, include_data=False, extra_tables=None, data_limit=10):
    tables = []
    rows = safe_fetch(cursor, """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """, (schema_name,))
    for (table_name,) in rows:
        comment = None
        try:
            cursor.execute("SELECT obj_description('%s.%s'::regclass)", (schema_name, table_name))
            row = cursor.fetchone()
            if row:
                comment = row[0]
        except:
            pass
        columns = []
        col_rows = safe_fetch(cursor, """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))
        for col in col_rows:
            col_name, data_type, is_nullable, col_default = col
            col_comment = None
            try:
                cursor.execute("""
                    SELECT col_description(('%s.%s'::regclass), ordinal_position)
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s AND column_name = %s
                """, (schema_name, table_name, schema_name, table_name, col_name))
                cc = cursor.fetchone()
                if cc:
                    col_comment = cc[0]
            except:
                pass
            columns.append({
                "name": col_name,
                "data_type": data_type,
                "nullable": is_nullable == 'YES',
                "default": col_default,
                "comment": col_comment
            })
        pk_rows = safe_fetch(cursor, """
            SELECT kc.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kc
                ON tc.constraint_name = kc.constraint_name
                AND tc.table_schema = kc.table_schema
            WHERE tc.table_schema = %s AND tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kc.ordinal_position
        """, (schema_name, table_name))
        pk = [row[0] for row in pk_rows]
        fk_rows = safe_fetch(cursor, """
            SELECT kc.column_name, ccu.table_schema, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kc
                ON tc.constraint_name = kc.constraint_name
                AND tc.table_schema = kc.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = %s AND tc.table_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
        """, (schema_name, table_name))
        fk = [{"column": r[0], "ref_table": f"{r[1]}.{r[2]}", "ref_column": r[3]} for r in fk_rows]

        # Данные
        table_data = None
        if include_data or (extra_tables and f"{schema_name}.{table_name}" in extra_tables):
            try:
                cursor.execute(sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                ), (data_limit,))
                rows_data = cursor.fetchall()
                if rows_data:
                    cols = [desc[0] for desc in cursor.description]
                    data_rows = []
                    for row in rows_data:
                        row_dict = {}
                        for i, col in enumerate(cols):
                            val = row[i]
                            if isinstance(val, (datetime, date, time, Decimal)):
                                val = json_serializer(val)
                            row_dict[col] = val
                        data_rows.append(row_dict)
                    table_data = data_rows
            except Exception as e:
                print(f"      Ошибка выгрузки данных {schema_name}.{table_name}: {e}")
                table_data = None

        tables.append({
            "name": table_name,
            "comment": comment,
            "columns": columns,
            "primary_key": pk,
            "foreign_keys": fk,
            "data": table_data
        })
    return tables

def get_views_metadata(cursor, schema_name):
    views = []
    rows = safe_fetch(cursor, """
        SELECT table_name, view_definition
        FROM information_schema.views
        WHERE table_schema = %s
        ORDER BY table_name
    """, (schema_name,))
    for view_name, definition in rows:
        comment = None
        try:
            cursor.execute("SELECT obj_description('%s.%s'::regclass)", (schema_name, view_name))
            row = cursor.fetchone()
            if row:
                comment = row[0]
        except:
            pass
        columns = []
        col_rows = safe_fetch(cursor, """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, view_name))
        columns = [{"name": r[0], "data_type": r[1]} for r in col_rows]
        views.append({
            "name": view_name,
            "definition": definition,
            "columns": columns,
            "comment": comment
        })
    return views

def get_functions_metadata(cursor, schema_name):
    rows = safe_fetch(cursor, """
        SELECT p.proname, pg_get_function_arguments(p.oid), pg_get_function_result(p.oid),
               pg_get_functiondef(p.oid), obj_description(p.oid), p.prokind
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = %s
        ORDER BY p.proname
    """, (schema_name,))
    functions = []
    for row in rows:
        functions.append({
            "name": row[0],
            "arguments": row[1],
            "result_type": row[2] if row[2] else "void",
            "definition": row[3],
            "comment": row[4],
            "kind": "procedure" if row[5] == 'p' else "function"
        })
    return functions

def get_indexes_metadata(cursor, schema_name):
    rows = safe_fetch(cursor, """
        SELECT i.relname, t.relname, pg_get_indexdef(idx.indexrelid), idx.indisunique, am.amname
        FROM pg_index idx
        JOIN pg_class i ON idx.indexrelid = i.oid
        JOIN pg_class t ON idx.indrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        JOIN pg_am am ON i.relam = am.oid
        WHERE n.nspname = %s
        ORDER BY i.relname
    """, (schema_name,))
    indexes = []
    for idx_name, table_name, definition, is_unique, method in rows:
        indexes.append({
            "name": idx_name,
            "table": f"{schema_name}.{table_name}",
            "definition": definition,
            "unique": is_unique,
            "method": method
        })
    return indexes

def draw_text(c, text, x, y, font_name, font_size, max_width, leading, margin_bottom):
    """Рисует текст с переносом строк, возвращает новую y."""
    c.setFont(font_name, font_size)
    lines = []
    for para in text.splitlines():
        if c.stringWidth(para, font_name, font_size) <= max_width:
            lines.append(para)
        else:
            words = para.split(' ')
            cur = ''
            for w in words:
                test = cur + (' ' if cur else '') + w
                if c.stringWidth(test, font_name, font_size) <= max_width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
    for line in lines:
        if y - leading < margin_bottom:
            c.showPage()
            c.setFont(font_name, font_size)
            y = A4[1] - 20*mm
        c.drawString(x, y, line)
        y -= leading
    return y

def generate_pdf(schema_data, output_file):
    c = canvas.Canvas(output_file, pagesize=A4)
    page_width, page_height = A4
    margin_top = 20 * mm
    margin_left = 15 * mm
    margin_right = 15 * mm
    margin_bottom = 20 * mm
    text_width = page_width - margin_left - margin_right
    y = page_height - margin_top
    font_normal = CYRILLIC_FONT
    font_bold = CYRILLIC_FONT
    size_title = 16
    size_schema = 14
    size_table = 12
    size_text = 9
    leading = 4

    c.setFont(font_bold, size_title)
    c.drawString(margin_left, y, "PostgreSQL Database Structure Export")
    y -= 10
    c.setFont(font_normal, size_text)
    y = draw_text(c, f"Generated: {datetime.now().isoformat()}", margin_left, y,
                  font_normal, size_text, text_width, leading, margin_bottom)

    for schema_name, schema in schema_data.items():
        if y < margin_bottom + 20:
            c.showPage()
            y = page_height - margin_top
        c.setFont(font_bold, size_schema)
        c.setFillColor(blue)
        c.drawString(margin_left, y, f"Schema: {schema_name}")
        y -= 8
        c.setFillColor(black)
        c.setFont(font_normal, size_text)
        if schema.get('comment'):
            y = draw_text(c, f"Comment: {schema['comment']}", margin_left, y,
                          font_normal, size_text, text_width, leading, margin_bottom)
            y -= 2
        # Таблицы
        for table in schema.get('tables', []):
            if y < margin_bottom + 40:
                c.showPage()
                y = page_height - margin_top
            c.setFont(font_bold, size_table)
            c.drawString(margin_left, y, f"Table: {table['name']}")
            y -= 6
            c.setFont(font_normal, size_text)
            if table.get('comment'):
                y = draw_text(c, f"  Comment: {table['comment']}", margin_left, y,
                              font_normal, size_text, text_width, leading, margin_bottom)
            # Колонки
            y = draw_text(c, "  Columns:", margin_left, y,
                          font_normal, size_text, text_width, leading, margin_bottom)
            for col in table['columns']:
                col_str = f"    {col['name']} {col['data_type']}"
                if not col['nullable']:
                    col_str += " NOT NULL"
                if col['default']:
                    col_str += f" DEFAULT {col['default']}"
                if col.get('comment'):
                    col_str += f"  -- {col['comment']}"
                y = draw_text(c, col_str, margin_left, y,
                              font_normal, size_text, text_width, leading, margin_bottom)
            # PK
            if table['primary_key']:
                y = draw_text(c, f"  Primary Key: {', '.join(table['primary_key'])}", margin_left, y,
                              font_normal, size_text, text_width, leading, margin_bottom)
            # FK
            for fk in table['foreign_keys']:
                y = draw_text(c, f"  Foreign Key: {fk['column']} -> {fk['ref_table']}.{fk['ref_column']}", margin_left, y,
                              font_normal, size_text, text_width, leading, margin_bottom)
            # Данные
            if table.get('data'):
                y = draw_text(c, f"  Sample Data (max {len(table['data'])} rows):", margin_left, y,
                              font_normal, size_text, text_width, leading, margin_bottom)
                for row in table['data']:
                    row_str = "    " + ", ".join(f"{k}={v}" for k, v in row.items())
                    y = draw_text(c, row_str[:120], margin_left, y,
                                  font_normal, size_text, text_width, leading, margin_bottom)
            y -= 4
        # Индексы
        for idx in schema.get('indexes', []):
            if y < margin_bottom + 20:
                c.showPage()
                y = page_height - margin_top
            y = draw_text(c, f"Index: {idx['name']} on {idx['table']} ({idx['method']}) unique={idx['unique']}", margin_left, y,
                          font_normal, size_text, text_width, leading, margin_bottom)
        # Здесь можно добавить представления и функции, но для краткости опущено
        c.showPage()
        y = page_height - margin_top
    c.save()
    print(f"PDF сохранён: {output_file}")

def main():
    # Определяем схемы для обработки
    schemas_to_process = []
    for schema in ALL_SCHEMAS:
        flag = SCHEMAS_CONFIG.get(schema)
        if flag is not None:
            if flag == 1:
                schemas_to_process.append(schema)
        else:
            schemas_to_process.append(schema)

    # Определяем схемы для выгрузки данных
    schemas_to_load_data = set()
    extra_tables_set = set(EXTRA_DATA_TABLES)
    if ALL != -1:
        if ALL == 1:
            schemas_to_load_data = set(schemas_to_process)
        else:  # ALL == 0
            schemas_to_load_data = set(schemas_to_process) - {'data', 'ext'}
    else:
        # Если ALL=-1, данные не грузим ни для каких схем, но если указаны явные таблицы – грузим для них
        pass

    # Принудительно добавляем схемы для явных таблиц
    for tab in EXTRA_DATA_TABLES:
        if '.' in tab:
            sch, _ = tab.split('.', 1)
            if sch in schemas_to_process:
                schemas_to_load_data.add(sch)

    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    result = {}
    for schema in schemas_to_process:
        print(f"Обработка схемы: {schema}")
        include_data = (schema in schemas_to_load_data)
        tables = get_tables_metadata(cursor, schema, include_data=include_data, extra_tables=extra_tables_set, data_limit=DATA_LIMIT)
        views = get_views_metadata(cursor, schema)
        functions = get_functions_metadata(cursor, schema)
        indexes = get_indexes_metadata(cursor, schema)
        result[schema] = {
            "comment": get_schema_comment(cursor, schema),
            "tables": tables,
            "views": views,
            "functions": functions,
            "indexes": indexes
        }
    cursor.close()
    conn.close()
    generate_pdf(result, OUTPUT_FILE)

if __name__ == "__main__":
    main()