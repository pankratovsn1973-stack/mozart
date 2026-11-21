# Файл: /home/sergey/Documents/configurate/database.py
import psycopg2
from ide_core import goProject


class DatabaseService:
    """Единый класс для взаимодействия с БД, обёртка над goProject."""

    def __init__(self):
        pass

    def execute_query(self, sql, params=None, fetch=True):
        """Выполнить SQL-запрос (SELECT или модифицирующий)."""
        # Гарантированно берем коннект psycopg2 из ядра
        conn = goProject.db_conn

        # Проверяем, что это действительно объект соединения, а не DatabaseService или None
        if conn is None or isinstance(conn, DatabaseService):
            print("DB Error: Нет активного соединения с БД или структура ядра нарушена!")
            return [] if fetch else False

        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch and cur.description:
                    return cur.fetchall()
                return True
        except Exception as e:
            print(f"DB Error: {e}")
            if fetch:
                return []
            raise

    def execute_procedure(self, proc_name, params=None):
        if params:
            placeholders = ','.join(['%s'] * len(params))
            sql = f"CALL {proc_name}({placeholders})"
        else:
            sql = f"CALL {proc_name}()"
        return self.execute_query(sql, params, fetch=False)

    def get_connection(self):
        return goProject.db_conn

    def refresh_connection(self):
        pass
