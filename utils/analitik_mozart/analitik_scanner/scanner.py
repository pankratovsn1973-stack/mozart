# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_scanner/scanner.py
"""
Сканер файловой системы для Аналитика Моцарт.
Версия: 2.1 — исправлены JSONB запросы
"""
# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_scanner/scanner.py
"""
Сканер файловой системы для Аналитика Моцарт.
Версия: 2.2 — исправлен импорт JSONB
"""

import os
import hashlib
import json
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB  # <-- ИСПРАВЛЕНО

from analitik_core.database import get_session, get_db
from analitik_core.models import Entity, EntityType


# ... остальной код без изменений ...

class ProjectScanner:
    """
    Сканирует файловую систему проекта.
    Собирает информацию о каталогах и файлах для загрузки в Entity.
    """

    def __init__(self, project_root: str, db_session: Session = None):
        self.project_root = os.path.abspath(project_root)
        self.db_session = db_session or get_session()
        self.db = get_db()

        # Настройки игнорирования
        self.ignore_dirs = {
            '.venv', 'venv', 'env', '.env',
            '.git', '.svn', '.hg',
            '__pycache__', '.pytest_cache', '.mypy_cache',
            '.idea', '.vscode',
            'node_modules', 'build', 'dist',
            '.tox', '.ipynb_checkpoints',
            '.DS_Store', 'Thumbs.db',
            'logs', 'backup', 'old', 'tmp', 'backups'
        }
        self.ignore_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.dylib',
            '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
        }

        # Статистика
        self._stats = {
            'directories': 0,
            'files': 0,
            'python_files': 0,
            'errors': 0,
            'skipped': 0
        }

        # Кэш для быстрого поиска
        self._entity_cache = {}
        self._path_cache = {}

    def scan(self) -> Dict[str, int]:
        """Запускает сканирование проекта."""
        print(f"🔍 Сканирование проекта: {self.project_root}")
        print("=" * 60)

        # Очищаем кэш
        self._entity_cache = {}
        self._path_cache = {}

        # Начинаем с корневого каталога
        root_entity = self._get_or_create_root_directory()

        if root_entity:
            # Сканируем содержимое корневого каталога
            self._scan_directory(self.project_root, root_entity.id, 0)

        self.db_session.commit()

        print("=" * 60)
        print(f"📊 СТАТИСТИКА СКАНИРОВАНИЯ:")
        print(f"  📁 Каталогов: {self._stats['directories']}")
        print(f"  📄 Файлов всего: {self._stats['files']}")
        print(f"  🐍 Python файлов: {self._stats['python_files']}")
        if self._stats['skipped'] > 0:
            print(f"  ⏭️ Пропущено (игнорируется): {self._stats['skipped']}")
        if self._stats['errors'] > 0:
            print(f"  ❌ Ошибок: {self._stats['errors']}")

        return self._stats

    # ================================================================
    # РАБОТА С КОРНЕВЫМ КАТАЛОГОМ
    # ================================================================

    def _get_or_create_root_directory(self) -> Optional[Entity]:
        """Получает или создаёт корневой каталог проекта."""
        root_name = os.path.basename(self.project_root)

        # Ищем существующий корневой каталог (без родителя)
        existing = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.parent_id.is_(None),  # <-- ИСПРАВЛЕНО: без JSONB
            Entity.is_active == True
        ).first()

        # Проверяем, что это тот же путь
        if existing and existing.j_data:
            if existing.j_data.get('full_path') == self.project_root:
                return existing

        # Если нашли с другим путём — закрываем
        if existing:
            existing.is_active = False
            existing.dt_end = datetime.now()
            self.db_session.flush()

        # Создаём новый корневой каталог
        root = Entity(
            type_id=EntityType.DIRECTORY,
            c_name=root_name,
            j_data={
                "full_path": self.project_root,
                "is_root": True
            },
            m_comment=f"Корень проекта: {self.project_root}"
        )
        self.db_session.add(root)
        self.db_session.flush()

        self._stats['directories'] += 1
        self._entity_cache[self.project_root] = root.id

        return root

    # ================================================================
    # СКАНИРОВАНИЕ ДИРЕКТОРИЙ
    # ================================================================

    def _scan_directory(self, dir_path: str, parent_id: str, level: int) -> Optional[str]:
        """
        Сканирует один каталог рекурсивно.
        """
        try:
            dir_name = os.path.basename(dir_path)

            # Пропускаем игнорируемые каталоги
            if dir_name in self.ignore_dirs:
                self._stats['skipped'] += 1
                return None

            # Создаём или получаем каталог
            dir_entity = self._get_or_create_directory(dir_path, dir_name, parent_id)
            if not dir_entity:
                return None

            # Получаем содержимое каталога
            try:
                items = os.listdir(dir_path)
            except PermissionError:
                print(f"  ⚠️ Нет доступа к каталогу: {dir_path}")
                self._stats['errors'] += 1
                return str(dir_entity.id)

            # Разделяем на каталоги и файлы
            dirs = []
            files = []
            for item in items:
                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    dirs.append((item, full_path))
                elif os.path.isfile(full_path):
                    files.append((item, full_path))

            # Сначала обрабатываем файлы
            for filename, full_path in files:
                self._process_file(full_path, filename, dir_entity.id)

            # Затем рекурсивно обрабатываем подкаталоги
            for dirname, full_path in sorted(dirs):
                self._scan_directory(full_path, dir_entity.id, level + 1)

            return str(dir_entity.id)

        except Exception as e:
            print(f"  ❌ Ошибка сканирования {dir_path}: {e}")
            self._stats['errors'] += 1
            return None

    def _get_or_create_directory(self, full_path: str, name: str, parent_id: Optional[str]) -> Optional[Entity]:
        """Получает или создаёт запись о каталоге."""
        # Проверяем кэш
        cache_key = f"dir_{full_path}"
        if cache_key in self._entity_cache:
            entity_id = self._entity_cache[cache_key]
            return self.db_session.query(Entity).filter(Entity.id == entity_id).first()

        # Ищем существующий активный каталог — ищем по parent_id и имени
        existing = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.c_name == name,
            Entity.parent_id == parent_id,
            Entity.is_active == True
        ).first()

        # Проверяем путь
        if existing and existing.j_data:
            if existing.j_data.get('full_path') == full_path:
                self._entity_cache[cache_key] = existing.id
                return existing

        # Если нашли с другим путём — закрываем
        if existing:
            existing.is_active = False
            existing.dt_end = datetime.now()
            self.db_session.flush()

        # Проверяем, не было ли закрытых версий
        closed = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.c_name == name,
            Entity.parent_id == parent_id,
            Entity.is_active == False
        ).order_by(Entity.dt_start.desc()).first()

        # Создаём новый каталог
        entity = Entity(
            type_id=EntityType.DIRECTORY,
            c_name=name,
            parent_id=parent_id,
            j_data={"full_path": full_path},
            n_old_version=closed.id if closed else None
        )
        self.db_session.add(entity)
        self.db_session.flush()

        self._stats['directories'] += 1
        self._entity_cache[cache_key] = entity.id

        # Выводим прогресс
        if self._stats['directories'] % 50 == 0:
            print(f"  📁 Каталогов: {self._stats['directories']}")

        return entity

    # ================================================================
    # ОБРАБОТКА ФАЙЛОВ
    # ================================================================

    def _process_file(self, full_path: str, filename: str, directory_id: Optional[str]):
        """Обрабатывает один файл."""
        ext = os.path.splitext(filename)[1].lower()

        # Пропускаем игнорируемые расширения
        if ext in self.ignore_extensions:
            self._stats['skipped'] += 1
            return

        # Проверяем, является ли файл Python
        is_python = ext == '.py'

        try:
            # Получаем информацию о файле
            stat = os.stat(full_path)
            size = stat.st_size
            mtime = stat.st_mtime

            # Вычисляем MD5 только для небольших файлов
            if size < 1024 * 1024:  # < 1MB
                hash_md5 = self._calc_md5(full_path)
            else:
                hash_md5 = None

            # Создаём или обновляем запись
            file_entity = self._upsert_file(
                full_path=full_path,
                filename=filename,
                extension=ext,
                is_python=is_python,
                size_bytes=size,
                hash_md5=hash_md5,
                mtime=mtime,
                directory_id=directory_id
            )

            self._stats['files'] += 1
            if is_python:
                self._stats['python_files'] += 1

            # Выводим прогресс
            if self._stats['files'] % 100 == 0:
                print(f"  📄 Обработано файлов: {self._stats['files']}")

        except Exception as e:
            print(f"  ❌ Ошибка обработки {full_path}: {e}")
            self._stats['errors'] += 1

    def _upsert_file(self, full_path: str, filename: str, extension: str,
                     is_python: bool, size_bytes: int, hash_md5: Optional[str],
                     mtime: float, directory_id: Optional[str]) -> Optional[Entity]:
        """Создаёт или обновляет запись о файле."""
        # Проверяем кэш
        cache_key = f"file_{full_path}"
        if cache_key in self._entity_cache:
            entity_id = self._entity_cache[cache_key]
            existing = self.db_session.query(Entity).filter(Entity.id == entity_id).first()
            if existing and existing.is_active:
                old_size = existing.j_data.get('size_bytes') if existing.j_data else None
                old_hash = existing.j_data.get('hash_md5') if existing.j_data else None
                if old_size == size_bytes and old_hash == hash_md5:
                    return existing

        # Ищем существующий активный файл — по имени и родителю
        existing = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.c_name == filename,
            Entity.parent_id == directory_id,
            Entity.is_active == True
        ).first()

        # Проверяем путь
        if existing and existing.j_data:
            if existing.j_data.get('full_path') == full_path:
                old_size = existing.j_data.get('size_bytes') if existing.j_data else None
                old_hash = existing.j_data.get('hash_md5') if existing.j_data else None

                if old_size == size_bytes and old_hash == hash_md5:
                    self._entity_cache[cache_key] = existing.id
                    return existing

        # Если нашли с другим путём — закрываем
        if existing:
            existing.is_active = False
            existing.dt_end = datetime.now()
            self.db_session.flush()

        # Создаём новую версию файла
        j_data = {
            "extension": extension,
            "is_python": is_python,
            "size_bytes": size_bytes,
            "hash_md5": hash_md5,
            "full_path": full_path,
            "mtime": mtime
        }

        file_entity = Entity(
            type_id=EntityType.FILE,
            c_name=filename,
            parent_id=directory_id,
            j_data=j_data,
            n_old_version=existing.id if existing else None
        )
        self.db_session.add(file_entity)
        self.db_session.flush()

        self._entity_cache[cache_key] = file_entity.id

        return file_entity

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    def _calc_md5(self, file_path: str) -> str:
        """Вычисляет MD5-хэш файла."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _get_relative_path(self, full_path: str) -> str:
        """Возвращает путь относительно корня проекта."""
        try:
            return os.path.relpath(full_path, self.project_root)
        except ValueError:
            return full_path

    # ================================================================
    # ПУБЛИЧНЫЕ МЕТОДЫ
    # ================================================================

    def get_all_python_files(self) -> List[str]:
        """Возвращает список всех Python файлов в проекте."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Возвращает информацию о файле из БД."""
        # Ищем по имени и пути в j_data
        file_entity = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).all()

        for f in file_entity:
            if f.j_data and f.j_data.get('full_path') == file_path:
                return {
                    'id': str(f.id),
                    'name': f.c_name,
                    'path': f.j_data.get('full_path'),
                    'size': f.j_data.get('size_bytes'),
                    'hash': f.j_data.get('hash_md5'),
                    'is_python': f.j_data.get('is_python', False)
                }
        return None

    def get_directory_tree(self) -> List[Dict]:
        """Возвращает дерево каталогов проекта."""
        result = []
        root = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.parent_id.is_(None),
            Entity.is_active == True
        ).first()

        if root:
            result.append(self._get_directory_node(root))
        return result

    def _get_directory_node(self, entity: Entity) -> Dict:
        """Рекурсивно строит узел дерева каталогов."""
        children = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.parent_id == entity.id,
            Entity.is_active == True
        ).order_by(Entity.c_name).all()

        return {
            'id': str(entity.id),
            'name': entity.c_name,
            'path': entity.j_data.get('full_path') if entity.j_data else None,
            'children': [self._get_directory_node(child) for child in children],
            'file_count': self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.FILE,
                Entity.parent_id == entity.id,
                Entity.is_active == True
            ).count()
        }


# ================================================================
# УТИЛИТА
# ================================================================

def scan_project(project_root: str) -> Dict[str, int]:
    """Утилитарная функция для сканирования проекта."""
    scanner = ProjectScanner(project_root)
    return scanner.scan()


# ================================================================
# ТЕСТ
# ================================================================

if __name__ == "__main__":
    import sys
    from analitik_core.database import init_db

    print("=" * 60)
    print("🧪 ТЕСТ СКАНЕРА")
    print("=" * 60)

    if not init_db():
        print("❌ Не удалось подключиться к БД")
        sys.exit(1)

    project_root = "/home/sergey/Documents/configurate"
    stats = scan_project(project_root)

    print("\n✅ СКАНИРОВАНИЕ ЗАВЕРШЕНО!")