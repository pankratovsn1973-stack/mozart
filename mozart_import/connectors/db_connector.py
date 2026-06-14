# mozart_import/connectors/db_connector.py
import urllib.parse
import sqlite3
from typing import List, Dict, Any, Optional, Generator
from .base_connector import BaseConnector
from ..core.models import SourceSchema, SourceTable, SourceField, FieldType, SourceType

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

try:
    import cx_Oracle
    CX_ORACLE_AVAILABLE = True
except ImportError:
    CX_ORACLE_AVAILABLE = False


class DBConnector(BaseConnector):
    """
    Коннектор для реляционных баз данных: PostgreSQL, MySQL, MSSQL, Oracle, SQLite.
    Параметры подключения передаются через kwargs:
        db_type: 'postgresql', 'mysql', 'mssql', 'oracle', 'sqlite'
        host, port, database, user, password (для SQLite только database — путь к файлу)
    """
    def __init__(self, source_path: str, **kwargs):
        super().__init__(source_path, **kwargs)
        self.db_type = kwargs.get('db_type', 'postgresql')
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port')
        self.database = kwargs.get('database')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self._conn = None
        self._cursor = None

    def connect(self) -> bool:
        if self.db_type == 'postgresql':
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("Установите psycopg2: pip install psycopg2-binary")
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port or 5432,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self._cursor = self._conn.cursor()
        elif self.db_type == 'mysql':
            if not PYMYSQL_AVAILABLE:
                raise ImportError("Установите pymysql: pip install pymysql")
            self._conn = pymysql.connect(
                host=self.host,
                port=self.port or 3306,
                database=self.database,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            self._cursor = self._conn.cursor()
        elif self.db_type == 'mssql':
            if not PYODBC_AVAILABLE:
                raise ImportError("Установите pyodbc: pip install pyodbc")
            driver = '{ODBC Driver 17 for SQL Server}'
            conn_str = f"DRIVER={driver};SERVER={self.host},{self.port or 1433};DATABASE={self.database};UID={self.user};PWD={self.password}"
            self._conn = pyodbc.connect(conn_str)
            self._cursor = self._conn.cursor()
        elif self.db_type == 'oracle':
            if not CX_ORACLE_AVAILABLE:
                raise ImportError("Установите cx_Oracle: pip install cx-Oracle")
            dsn = cx_Oracle.makedsn(self.host, self.port or 1521, service_name=self.database)
            self._conn = cx_Oracle.connect(user=self.user, password=self.password, dsn=dsn)
            self._cursor = self._conn.cursor()
        elif self.db_type == 'sqlite':
            # Для SQLite database – путь к файлу
            if not self.database:
                raise ValueError("Для SQLite необходимо указать database (путь к файлу)")
            self._conn = sqlite3.connect(self.database)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
        else:
            raise ValueError(f"Неподдерживаемый тип БД: {self.db_type}")
        return True

    def disconnect(self) -> None:
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        self._cursor = None
        self._conn = None

    def _get_sqlite_schema(self) -> SourceSchema:
        # Получаем список таблиц (исключаем служебные)
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in self._cursor.fetchall()]
        source_tables = []
        for t in tables:
            self._cursor.execute(f"PRAGMA table_info('{t}')")
            cols = self._cursor.fetchall()
            fields = []
            for col in cols:
                col_name = col[1]
                col_type = col[2].upper()
                # Определяем тип поля
                if 'INT' in col_type:
                    ftype = FieldType.INTEGER
                    length = None
                elif 'REAL' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type:
                    ftype = FieldType.FLOAT
                    length = None
                elif 'CHAR' in col_type or 'TEXT' in col_type or 'CLOB' in col_type:
                    ftype = FieldType.STRING
                    length = None
                elif 'BLOB' in col_type:
                    ftype = FieldType.BINARY
                    length = None
                else:
                    ftype = FieldType.STRING
                    length = None
                fields.append(SourceField(
                    name=col_name,
                    field_type=ftype,
                    length=length,
                    nullable=not col[3]
                ))
            source_tables.append(SourceTable(name=t, fields=fields))
        return SourceSchema(
            source_type=SourceType.DATABASE,
            source_path=f"sqlite://{self.database}",
            tables=source_tables
        )

    def get_schema(self) -> SourceSchema:
        if self.db_type == 'postgresql':
            return self._get_postgresql_schema()
        elif self.db_type == 'sqlite':
            return self._get_sqlite_schema()
        # TODO: реализовать для MySQL, MSSQL, Oracle аналогично
        raise NotImplementedError(f"Получение схемы для {self.db_type} пока не реализовано")

    def get_table_sample(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        if self.db_type == 'sqlite':
            self._cursor.execute(f'SELECT * FROM "{table_name}" LIMIT ?', (limit,))
            rows = self._cursor.fetchall()
            columns = [desc[0] for desc in self._cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        else:
            self._cursor.execute(f'SELECT * FROM "{table_name}" LIMIT %s', (limit,))
            columns = [desc[0] for desc in self._cursor.description]
            rows = self._cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def iter_records(self, table_name: str, batch_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        if self.db_type == 'sqlite':
            offset = 0
            while True:
                self._cursor.execute(f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?', (batch_size, offset))
                rows = self._cursor.fetchall()
                if not rows:
                    break
                columns = [desc[0] for desc in self._cursor.description]
                batch = [dict(zip(columns, row)) for row in rows]
                yield batch
                offset += batch_size
                if len(rows) < batch_size:
                    break
        else:
            offset = 0
            while True:
                self._cursor.execute(f'SELECT * FROM "{table_name}" LIMIT %s OFFSET %s', (batch_size, offset))
                rows = self._cursor.fetchall()
                if not rows:
                    break
                columns = [desc[0] for desc in self._cursor.description]
                batch = [dict(zip(columns, row)) for row in rows]
                yield batch
                offset += batch_size
                if len(rows) < batch_size:
                    break

    def get_row_count(self, table_name: str) -> Optional[int]:
        self._cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        return self._cursor.fetchone()[0]