#database.py

import psycopg2
from ide_core import goProject


class DatabaseService:
    """Единый класс для взаимодействия с БД, обёртка над goProject."""

    def __init__(self):
        self._conn = goProject.db_conn

    def execute_query(self, sql, params=None, fetch=True):
        """Выполнить SQL-запрос (SELECT или модифицирующий)."""
        if fetch:
            return goProject.f_Execute(sql, params)
        else:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(sql, params)
                return True
            except Exception as e:
                print(f"DB Error: {e}")
                raise

    def execute_procedure(self, proc_name, params=None):
        if params:
            placeholders = ','.join(['%s'] * len(params))
            sql = f"CALL {proc_name}({placeholders})"
        else:
            sql = f"CALL {proc_name}()"
        return self.execute_query(sql, params, fetch=False)

    def get_connection(self):
        return self._conn

    def refresh_connection(self):
        self._conn = goProject.db_conn