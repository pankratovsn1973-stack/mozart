# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_core/database.py
"""
Подключение к базе данных и управление конфигурацией.
Версия: 4.3 — только подключение, без создания таблиц
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from analitik_core.models import Base


class Config:
    """Конфигурация проекта из db.mzt."""

    def __init__(self):
        self._config = None
        self._loaded = False
        self._config_file = None

    def load(self, config_file: str) -> bool:
        """Загружает конфигурацию из файла."""
        if not os.path.exists(config_file):
            return False

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            self._loaded = True
            self._config_file = config_file
            return True
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {config_file}: {e}")
            return False

    def is_loaded(self) -> bool:
        return self._loaded

    def get(self, key: str, default=None):
        """Получает значение по ключу (с поддержкой вложенности через точку)."""
        if not self._loaded:
            return default

        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_db_host(self) -> str:
        return self.get('db.host', 'localhost')

    def get_db_port(self) -> int:
        return int(self.get('db.port', 5432))

    def get_db_name(self) -> str:
        return self.get('db.name', 'mozart_erp')

    def get_db_user(self) -> str:
        return self.get('db.user', 'postgres')

    def get_db_password(self) -> str:
        return self.get('db.pass', '')

    def get_db_schema(self) -> str:
        return self.get('db.schema', 'mozart')

    def get_project_root(self) -> Optional[str]:
        return self.get('project.root')

    def get_ignore_dirs(self) -> List[str]:
        return self.get('project.ignore_dirs', [
            '__pycache__', '.git', '.svn', '.hg', '.idea', '.vscode',
            '.venv', 'venv', 'env', '.env', 'node_modules', 'build',
            'dist', '.pytest_cache', '.mypy_cache', '.tox',
            '.ipynb_checkpoints', '.DS_Store', 'Thumbs.db',
            'logs', 'backup', 'old', 'tmp', 'backups'
        ])

    def get_ignore_extensions(self) -> List[str]:
        return self.get('project.ignore_extensions', [
            '.pyc', '.pyo', '.so', '.dll', '.dylib',
            '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
        ])

    def get_include_only_python(self) -> bool:
        return self.get('project.include_only_python', True)

    def get_l2_path(self) -> Optional[str]:
        return self.get('l2.path')

    def get_l2_port(self) -> Optional[int]:
        return self.get('l2.port')

    def get_l3_path(self) -> Optional[str]:
        return self.get('l3.path')

    def get_l3_starter(self) -> Optional[str]:
        return self.get('l3.starter')

    def save_project_root(self, root_path: str) -> bool:
        if not self._loaded or not self._config:
            return False

        if 'project' not in self._config:
            self._config['project'] = {}
        self._config['project']['root'] = root_path

        return self._save()

    def save_schema(self, schema: str) -> bool:
        if not self._loaded or not self._config:
            return False

        if 'db' not in self._config:
            self._config['db'] = {}
        self._config['db']['schema'] = schema

        return self._save()

    def _save(self) -> bool:
        if not self._config_file:
            return False

        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения {self._config_file}: {e}")
            return False


class AnalyticsDatabase:
    """Управление подключением к БД (только подключение, без создания таблиц)."""

    def __init__(
            self,
            config: Optional[Config] = None,
            pool_size: int = 5,
            max_overflow: int = 10,
            echo: bool = False
    ):
        self.config = config or Config()
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

        self.engine = None
        self.Session = None
        self._connected = False

    def load_config(self, config_file: str) -> bool:
        return self.config.load(config_file)

    def connect(self) -> bool:
        """Подключается к БД (без создания таблиц и функций)."""
        try:
            host = self.config.get_db_host()
            port = self.config.get_db_port()
            dbname = self.config.get_db_name()
            user = self.config.get_db_user()
            password = self.config.get_db_password()
            schema = self.config.get_db_schema()

            dsn = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"

            self.engine = create_engine(
                dsn,
                echo=self.echo,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 10,
                    'options': f'-c search_path={schema}'
                }
            )

            # Проверяем подключение
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print(f"✅ Подключено к {dbname}@{host}:{port}")

            # Проверяем, что схема существует
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
                    {'schema': schema}
                )
                if not result.fetchone():
                    print(f"⚠️ Схема {schema} не существует!")
                    print(f"   Создайте её через create_tables.sql")
                    return False

            self.Session = sessionmaker(bind=self.engine)
            self._connected = True

            return True

        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    # ========================================================================
    # РАБОТА С ХРАНИМЫМИ ФУНКЦИЯМИ
    # ========================================================================

    def get_entity_at_time(self, entity_id: str, dt: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Получает сущность на момент времени."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.get_entity_at_time(:id, :dt)"),
                {'id': entity_id, 'dt': dt}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def get_entity_tree(self, root_id: str, dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Получает дерево сущностей от корня."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.get_entity_tree(:root_id, :dt)"),
                {'root_id': root_id, 'dt': dt}
            )
            return [dict(row._mapping) for row in result]

    def get_entities_by_type(self, type_id: int, dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Получает все сущности определённого типа."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.get_entities_by_type(:type_id, :dt)"),
                {'type_id': type_id, 'dt': dt}
            )
            return [dict(row._mapping) for row in result]

    def get_entity_versions(self, entity_id: str) -> List[Dict[str, Any]]:
        """Получает все версии сущности."""
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.get_entity_versions(:id)"),
                {'id': entity_id}
            )
            return [dict(row._mapping) for row in result]

    def find_usages(self, entity_id: str, dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Находит использование сущности (кто вызывает)."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.find_usages(:id, :dt)"),
                {'id': entity_id, 'dt': dt}
            )
            return [dict(row._mapping) for row in result]

    def find_usage_chain(self, entity_id: str, max_depth: int = 5, dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Находит цепочку использований (рекурсивно)."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.find_usage_chain(:id, :max_depth, :dt)"),
                {'id': entity_id, 'max_depth': max_depth, 'dt': dt}
            )
            return [dict(row._mapping) for row in result]

    def get_task_entities(self, task_id: str, dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Получает все сущности, связанные с задачей."""
        if dt is None:
            dt = datetime.now()
        schema = self.config.get_db_schema()

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {schema}.get_task_entities(:task_id, :dt)"),
                {'task_id': task_id, 'dt': dt}
            )
            return [dict(row._mapping) for row in result]

    # ========================================================================
    # СЕССИЯ
    # ========================================================================

    def get_session(self) -> Session:
        if not self._connected:
            raise RuntimeError("База данных не подключена")
        return self.Session()

    def is_connected(self) -> bool:
        return self._connected

    def close(self):
        if self.engine:
            self.engine.dispose()
            self._connected = False
            print("🔒 Соединение с БД закрыто")


# ========================================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ========================================================================
_config = Config()
_db = None


def init_db(config_file: Optional[str] = None) -> bool:
    """
    Инициализирует БД (только подключение, без создания таблиц).
    """
    global _config, _db

    if config_file:
        if not _config.load(config_file):
            return False
    else:
        config_file = _find_config_file()
        if not config_file:
            print("❌ db.mzt не найден")
            return False
        if not _config.load(config_file):
            return False

    _db = AnalyticsDatabase(_config)
    return _db.connect()


def _find_config_file() -> Optional[str]:
    """Ищет db.mzt в стандартных местах."""
    candidates = [
        os.path.join(os.getcwd(), "db.mzt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db.mzt"),
        os.path.join(os.path.expanduser("~"), "Documents", "configurate", "db.mzt"),
        "/home/sergey/Documents/configurate/db.mzt",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def get_db() -> AnalyticsDatabase:
    global _db
    if _db is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_db()")
    return _db


def get_config() -> Config:
    return _config


def get_session() -> Session:
    return get_db().get_session()


def get_schema_name() -> str:
    return _config.get_db_schema()


def get_project_root() -> Optional[str]:
    return _config.get_project_root()


def get_ignore_dirs() -> List[str]:
    return _config.get_ignore_dirs()


def get_ignore_extensions() -> List[str]:
    return _config.get_ignore_extensions()


def get_include_only_python() -> bool:
    return _config.get_include_only_python()


# ========================================================================
# ТЕСТ
# ========================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К БД")
    print("=" * 60)

    if init_db():
        print("\n✅ БАЗА ДАННЫХ ГОТОВА К РАБОТЕ!")
        config = get_config()
        print(f"   Схема: {config.get_db_schema()}")
        print(f"   Корень проекта: {config.get_project_root()}")
        print(f"   Игнорируемых каталогов: {len(config.get_ignore_dirs())}")
        print(f"   Игнорируемых расширений: {len(config.get_ignore_extensions())}")
    else:
        print("❌ Не удалось подключиться к БД")
        sys.exit(1)