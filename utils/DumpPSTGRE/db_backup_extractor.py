# utils/db_backup_extractor.py
# -*- coding: utf-8 -*-

import os
import psycopg2
from psycopg2 import extras


class DbBackupExtractor:
    """Бэкэнд для извлечения метаданных, структуры, комментариев и данных из PostgreSQL."""

    def __init__(self, config):
        self.config = config

    def _get_connection(self):
        """Создает чистое подключение к целевой базе PostgreSQL."""
        return psycopg2.connect(**self.config)

    def fetch_db_structure(self):
        """Вытягивает из pg_catalog списки схем, таблиц, функций и представлений."""
        structure = {}
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            # 1. Читаем все кастомные схемы и их комментарии (описания)
            cursor.execute("""
                SELECT nspname as schema_name, d.description 
                FROM pg_namespace n
                LEFT JOIN pg_description d ON d.objoid = n.oid AND d.classoid = 'pg_namespace'::regclass
                WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND nspname NOT LIKE 'pg_temp%' AND nspname NOT LIKE 'pg_toast_temp%'
                ORDER BY nspname;
            """)
            schemas = cursor.fetchall()

            for s in schemas:
                s_name = s['schema_name']
                structure[s_name] = {
                    "description": s['description'] or "",
                    "tables": {}, "functions": {}, "views": {}
                }

                # 2. Читаем таблицы схемы
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = %s ORDER BY tablename;
                """, (s_name,))
                for t in cursor.fetchall():
                    structure[s_name]["tables"][t['tablename']] = {}

                # 3. Читаем представления (вьюхи) схемы
                cursor.execute("""
                    SELECT viewname FROM pg_views 
                    WHERE schemaname = %s ORDER BY viewname;
                """, (s_name,))
                for v in cursor.fetchall():
                    structure[s_name]["views"][v['viewname']] = {}

                # 4. Читаем функции и хранимые процедуры схемы
                cursor.execute("""
                    SELECT p.proname as func_name, pg_get_function_identity_arguments(p.oid) as args
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = %s ORDER BY p.proname;
                """, (s_name,))
                for f in cursor.fetchall():
                    f_identity = f"{f['func_name']}({f['args']})"
                    structure[s_name]["functions"][f_identity] = f['func_name']

        except Exception as e:
            print(f"Ошибка чтения структуры PostgreSQL: {str(e)}")
        finally:
            if conn:
                conn.close()
        return structure

    def generate_dump(self, file_path, dump_config):
        """Главный генератор дампа на основе выбранных чекбоксов дерева."""
        conn = None
        try:
            conn = self._get_connection()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("-- Mozart ERP Database Dump\n")
                f.write("-- Generated dynamically via DB Backup Tool\n\n")

                for schema, cfg in dump_config.items():
                    f.write(f"-- ==========================================\n")
                    f.write(f"-- СХЕМА: {schema}\n")
                    f.write(f"-- ==========================================\n\n")

                    if cfg.get("export_schema_desc") and cfg.get("schema_comment"):
                        f.write(f"COMMENT ON SCHEMA {schema} IS '{cfg['schema_comment']}';\n\n")

                    if cfg.get("views"):
                        self._dump_views(conn, f, schema, cfg["views"])

                    if cfg.get("tables"):
                        self._dump_tables_ddl(conn, f, schema, cfg["tables"], cfg)

                    if cfg.get("tables"):
                        self._dump_tables_data(conn, f, schema, cfg["tables"])

                    if cfg.get("functions"):
                        self._dump_functions(conn, f, schema, cfg["functions"])

            return True, "Дамп успешно сформирован!"
        except Exception as e:
            return False, f"Сбой генерации дампа:\n{str(e)}"
        finally:
            if conn:
                conn.close()

    def _dump_views(self, conn, f, schema, views):
        cursor = conn.cursor()
        for v in views:
            try:
                cursor.execute("SELECT pg_get_viewdef(%s::regclass, true);", (f"{schema}.{v}",))
                v_def = cursor.fetchone()
                f.write(f"CREATE OR REPLACE VIEW {schema}.{v} AS\n{v_def}\n\n")
            except Exception:
                continue

    def _dump_tables_ddl(self, conn, f, schema, tables, cfg):
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        for t, t_cfg in tables.items():
            full_table = f"{schema}.{t}"

            if t_cfg.get("structure"):
                f.write(f"CREATE TABLE {full_table} (\n")
                cursor.execute("""
                    SELECT column_name, data_type, character_maximum_length, is_nullable
                    FROM information_schema.columns WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position;
                """, (schema, t))
                cols = cursor.fetchall()
                col_lines = []
                for c in cols:
                    line = f"    {c['column_name']} {c['data_type']}"
                    if c['character_maximum_length']:
                        line += f"({c['character_maximum_length']})"
                    if c['is_nullable'] == 'NO':
                        line += " NOT NULL"
                    col_lines.append(line)
                f.write(",\n".join(col_lines))
                f.write("\n);\n\n")

            if t_cfg.get("description"):
                cursor.execute("SELECT obj_description(%s::regclass, 'pg_class');", (full_table,))
                t_desc = cursor.fetchone() if cursor.rowcount > 0 else None
                if t_desc:
                    f.write(f"COMMENT ON TABLE {full_table} IS '{t_desc}';\n")

                cursor.execute("""
                    SELECT cols.column_name, d.description
                    FROM pg_catalog.pg_stat_user_tables t
                    JOIN pg_catalog.pg_description d ON d.objoid = t.relid
                    JOIN information_schema.columns cols ON cols.table_schema = t.schemaname 
                        AND cols.table_name = t.relname AND cols.ordinal_position = d.objsubid
                    WHERE t.schemaname = %s AND t.relname = %s;
                """, (schema, t))
                for c_desc in cursor.fetchall():
                    f.write(f"COMMENT ON COLUMN {full_table}.{c_desc['column_name']} IS '{c_desc['description']}';\n")
                f.write("\n")

    def _dump_tables_data(self, conn, f, schema, tables):
        cursor = conn.cursor()
        for t, t_cfg in tables.items():
            if t_cfg.get("data"):
                full_table = f"{schema}.{t}"
                cursor.execute(f"SELECT * FROM {full_table};")
                rows = cursor.fetchall()
                if not rows:
                    continue

                # ИСПРАВЛЕНО: Извлекаем чистое текстовое имя из каждого объекта Column (desc[0])
                col_names = [desc[0] for desc in cursor.description]
                cols_str = ", ".join(col_names)

                f.write(f"-- Данные таблицы {full_table}\n")
                for row in rows:
                    vals = []
                    for val in row:
                        if val is None:
                            vals.append("NULL")
                        elif isinstance(val, (int, float)):
                            vals.append(str(val))
                        else:
                            vals.append(f"'{str(val).replace(chr(39), chr(39) + chr(39))}'")
                    f.write(f"INSERT INTO {full_table} ({cols_str}) VALUES ({', '.join(vals)});\n")
                f.write("\n")

    def _dump_functions(self, conn, f, schema, functions):
        cursor = conn.cursor()
        for f_identity, f_name in functions.items():
            try:
                cursor.execute("""
                    SELECT pg_get_functiondef(p.oid)
                    FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = %s AND p.proname = %s;
                """, (schema, f_name))
                f_def = cursor.fetchone()
                f.write(f"{f_def}\n\n")
            except Exception:
                continue
