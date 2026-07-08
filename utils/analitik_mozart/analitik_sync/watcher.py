# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_sync/watcher.py
"""
Наблюдатель за изменениями файлов для автоматической синхронизации.
Версия: 2.0 — для единой таблицы сущностей
"""

import os
import time
import hashlib
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from analitik_core.database import get_db, get_session
from analitik_core.models import Entity, EntityType
from analitik_core.parser import PythonParser
from analitik_core.description_loader import DescriptionLoader
from analitik_scanner.loader import DataLoader


class CodeChangeHandler(FileSystemEventHandler):
    """
    Обработчик изменений файлов в реальном времени.
    Отслеживает изменения в файловой системе и синхронизирует их с БД.
    """

    def __init__(
            self,
            project_root: str,
            db_session=None,
            callback: Optional[Callable] = None,
            debounce_delay: float = 0.5
    ):
        self.project_root = os.path.abspath(project_root)
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.callback = callback
        self.debounce_delay = debounce_delay

        self.parser = PythonParser()
        self.description_loader = DescriptionLoader()
        self.loader = DataLoader(project_root, self.db_session)

        # Кэш для последних изменений (debounce)
        self._last_modified = {}
        self._pending_changes = {}
        self._processing = False

        # Статистика
        self.stats = {
            'modified': 0,
            'created': 0,
            'deleted': 0,
            'errors': 0,
            'ignored': 0
        }

    def on_modified(self, event: FileSystemEvent):
        """Обработка изменения файла."""
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        current_time = time.time()
        if event.src_path in self._last_modified:
            if current_time - self._last_modified[event.src_path] < self.debounce_delay:
                return

        self._last_modified[event.src_path] = current_time

        # Откладываем обработку для debounce
        if event.src_path in self._pending_changes:
            return

        self._pending_changes[event.src_path] = {
            'type': 'modified',
            'time': current_time
        }

        # Запускаем обработку с задержкой
        time.sleep(self.debounce_delay)
        self._process_pending()

    def on_created(self, event: FileSystemEvent):
        """Обработка создания файла."""
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        self._pending_changes[event.src_path] = {
            'type': 'created',
            'time': time.time()
        }

        time.sleep(0.2)  # Небольшая задержка для завершения записи
        self._process_pending()

    def on_deleted(self, event: FileSystemEvent):
        """Обработка удаления файла."""
        if event.is_directory:
            return

        if not event.src_path.endswith('.py'):
            return

        self._pending_changes[event.src_path] = {
            'type': 'deleted',
            'time': time.time()
        }

        self._process_pending()

    def _should_process(self, file_path: str) -> bool:
        """Проверяет, нужно ли обрабатывать файл."""
        # Только Python файлы
        if not file_path.endswith('.py'):
            return False

        # Игнорируем временные файлы
        if file_path.endswith('~') or file_path.endswith('.pyc'):
            return False

        # Игнорируем файлы в игнорируемых директориях
        rel_path = os.path.relpath(file_path, self.project_root)
        path_parts = Path(rel_path).parts

        ignore_dirs = {
            '__pycache__', '.git', '.svn', '.hg',
            '.venv', 'venv', 'env', '.env',
            '.idea', '.vscode', 'node_modules',
            'build', 'dist', '.tox', '.pytest_cache',
            '.mypy_cache', '.ipynb_checkpoints',
            '.DS_Store', 'Thumbs.db', 'logs',
            'backup', 'old', 'tmp', 'backups'
        }

        for part in path_parts:
            if part in ignore_dirs:
                return False

        return True

    def _process_pending(self):
        """Обрабатывает накопленные изменения."""
        if self._processing:
            return

        self._processing = True

        try:
            # Копируем и очищаем pending
            pending = dict(self._pending_changes)
            self._pending_changes = {}

            for file_path, change in pending.items():
                change_type = change.get('type')

                if change_type == 'deleted':
                    self._handle_deleted(file_path)
                elif change_type == 'created':
                    self._handle_created(file_path)
                elif change_type == 'modified':
                    self._handle_modified(file_path)

        except Exception as e:
            if self.callback:
                self.callback('error', 'processing', str(e))
            self.stats['errors'] += 1

        finally:
            self._processing = False

    def _handle_modified(self, file_path: str):
        """Обрабатывает изменение файла."""
        try:
            if not os.path.exists(file_path):
                return

            rel_path = os.path.relpath(file_path, self.project_root)

            # Читаем содержимое
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Парсим файл
            parse_result = self.parser.parse_file(file_path, content)

            # Обогащаем описаниями
            self._enrich_with_descriptions(file_path, parse_result)

            # Находим файл в БД
            file_entity = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.FILE,
                Entity.j_data.contains({"full_path": file_path}),
                Entity.is_active == True
            ).first()

            if file_entity:
                # Проверяем, изменился ли файл
                old_hash = file_entity.j_data.get('hash_md5') if file_entity.j_data else None
                new_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

                if old_hash == new_hash and file_entity.t_blobskript is not None:
                    # Файл не изменился по сути (только метаданные)
                    return

                # Обновляем файл
                self._update_file(file_entity, parse_result, content)

                if self.callback:
                    self.callback('modified', rel_path, {
                        'file': os.path.basename(file_path),
                        'classes': len(parse_result.get('classes', [])),
                        'procedures': len(parse_result.get('procedures', [])),
                        'variables': len(parse_result.get('global_variables', []))
                    })

                self.stats['modified'] += 1

            else:
                # Файл ещё не в БД — создаём
                self._handle_created(file_path)

        except Exception as e:
            if self.callback:
                self.callback('error', file_path, str(e))
            self.stats['errors'] += 1

    def _handle_created(self, file_path: str):
        """Обрабатывает создание файла."""
        try:
            if not os.path.exists(file_path):
                return

            rel_path = os.path.relpath(file_path, self.project_root)

            # Создаём файл через сканер
            dir_path = os.path.dirname(file_path)
            dir_entity = self._get_or_create_directory(dir_path)

            if dir_entity:
                self.loader.scanner._process_file(
                    dir_path,
                    os.path.basename(file_path),
                    dir_entity.id
                )
                self.db_session.commit()

                if self.callback:
                    self.callback('created', rel_path, {
                        'file': os.path.basename(file_path)
                    })

                self.stats['created'] += 1

        except Exception as e:
            if self.callback:
                self.callback('error', file_path, str(e))
            self.stats['errors'] += 1

    def _handle_deleted(self, file_path: str):
        """Обрабатывает удаление файла."""
        try:
            rel_path = os.path.relpath(file_path, self.project_root)

            # Находим файл в БД
            file_entity = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.FILE,
                Entity.j_data.contains({"full_path": file_path}),
                Entity.is_active == True
            ).first()

            if file_entity:
                # Закрываем файл
                file_entity.is_active = False
                file_entity.dt_end = datetime.now()

                # Закрываем все дочерние сущности
                self.db_session.query(Entity).filter(
                    Entity.parent_id == file_entity.id,
                    Entity.is_active == True
                ).update({
                    'is_active': False,
                    'dt_end': datetime.now()
                })

                self.db_session.commit()

                if self.callback:
                    self.callback('deleted', rel_path, {
                        'file': os.path.basename(file_path)
                    })

                self.stats['deleted'] += 1

        except Exception as e:
            if self.callback:
                self.callback('error', file_path, str(e))
            self.stats['errors'] += 1

    def _update_file(self, file_entity: Entity, parse_result: Dict, content: str):
        """Обновляет файл в БД."""
        # Закрываем старую версию
        file_entity.is_active = False
        file_entity.dt_end = datetime.now()

        # Создаём новую версию
        new_file = Entity(
            type_id=EntityType.FILE,
            c_name=file_entity.c_name,
            parent_id=file_entity.parent_id,
            j_data=file_entity.j_data.copy() if file_entity.j_data else {},
            n_old_version=file_entity.id
        )

        # Обновляем данные
        if new_file.j_data:
            new_file.j_data['hash_md5'] = hashlib.md5(content.encode('utf-8')).hexdigest()
            new_file.j_data['size_bytes'] = len(content.encode('utf-8'))
            new_file.j_data['mtime'] = os.path.getmtime(file_entity.j_data.get('full_path', ''))

        if parse_result.get('description'):
            new_file.m_comment = parse_result['description']

        self.db_session.add(new_file)
        self.db_session.flush()

        # Закрываем старые дочерние сущности
        self.db_session.query(Entity).filter(
            Entity.parent_id == new_file.id,
            Entity.is_active == True
        ).update({
            'is_active': False,
            'dt_end': datetime.now()
        })

        # Загружаем новую структуру
        self.loader._load_file_structure(new_file.id, parse_result.get('file_path', ''), parse_result)

        self.db_session.commit()

    def _enrich_with_descriptions(self, file_path: str, parse_result: Dict):
        """Обогащает результат парсинга описаниями."""
        desc = self.description_loader.get_file_description(file_path)
        if desc.get('description'):
            parse_result['description'] = desc['description']

        # Описания классов
        for cls_data in parse_result.get('classes', []):
            class_desc = self.description_loader.get_class_description(
                file_path, cls_data['name']
            )
            if class_desc.get('description'):
                cls_data['description'] = class_desc['description']

        # Описания процедур
        for proc_data in parse_result.get('procedures', []):
            func_desc = self.description_loader.get_function_description(
                file_path, proc_data['name']
            )
            if func_desc.get('description'):
                proc_data['description'] = func_desc['description']

    def _get_or_create_directory(self, dir_path: str) -> Optional[Entity]:
        """Получает или создаёт каталог."""
        # Ищем существующий
        existing = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.j_data.contains({"full_path": dir_path}),
            Entity.is_active == True
        ).first()

        if existing:
            return existing

        # Создаём новый
        parent_path = os.path.dirname(dir_path)
        parent_entity = None

        if parent_path and parent_path != dir_path:
            parent_entity = self._get_or_create_directory(parent_path)

        entity = Entity(
            type_id=EntityType.DIRECTORY,
            c_name=os.path.basename(dir_path),
            parent_id=parent_entity.id if parent_entity else None,
            j_data={"full_path": dir_path}
        )
        self.db_session.add(entity)
        self.db_session.flush()

        return entity

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику."""
        return self.stats.copy()

    def reset_stats(self):
        """Сбрасывает статистику."""
        self.stats = {
            'modified': 0,
            'created': 0,
            'deleted': 0,
            'errors': 0,
            'ignored': 0
        }


class SyncManager:
    """
    Менеджер синхронизации — запуск и остановка наблюдателя.
    """

    def __init__(self, project_root: str, db_session=None):
        self.project_root = os.path.abspath(project_root)
        self.db_session = db_session or get_session()
        self.observer = None
        self.handler = None
        self._callback = None
        self._running = False

    def start(self, callback: Optional[Callable] = None) -> bool:
        """
        Запускает наблюдатель за изменениями.

        Args:
            callback: Функция обратного вызова с сигнатурами:
                - ('started', project_root, {'status': 'running'})
                - ('modified', rel_path, {'file': name, ...})
                - ('created', rel_path, {'file': name})
                - ('deleted', rel_path, {'file': name})
                - ('error', path, error_message)
                - ('stopped', project_root, {'status': 'stopped'})
        """
        if self._running:
            return False

        if not os.path.exists(self.project_root):
            if callback:
                callback('error', self.project_root, 'Проект не найден')
            return False

        try:
            self._callback = callback
            self.handler = CodeChangeHandler(
                self.project_root,
                self.db_session,
                callback,
                debounce_delay=0.5
            )

            self.observer = Observer()
            self.observer.schedule(self.handler, self.project_root, recursive=True)
            self.observer.start()
            self._running = True

            if callback:
                callback('started', self.project_root, {'status': 'running'})

            return True

        except Exception as e:
            if callback:
                callback('error', self.project_root, str(e))
            return False

    def stop(self):
        """Останавливает наблюдатель."""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._running = False

        if self._callback:
            self._callback('stopped', self.project_root, {'status': 'stopped'})

    def is_running(self) -> bool:
        """Проверяет, запущен ли наблюдатель."""
        return self._running

    def get_status(self) -> Dict:
        """Возвращает статус синхронизации."""
        return {
            'running': self._running,
            'project_root': self.project_root,
            'observer_active': self.observer is not None and self.observer.is_alive(),
            'stats': self.handler.get_stats() if self.handler else {}
        }

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику изменений."""
        if self.handler:
            return self.handler.get_stats()
        return {
            'modified': 0,
            'created': 0,
            'deleted': 0,
            'errors': 0,
            'ignored': 0
        }

    def reset_stats(self):
        """Сбрасывает статистику."""
        if self.handler:
            self.handler.reset_stats()


# ================================================================
# УТИЛИТА ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def sync_project(project_root: str, callback: Optional[Callable] = None) -> SyncManager:
    """
    Быстрый запуск синхронизации проекта.

    Args:
        project_root: Корень проекта
        callback: Функция обратного вызова

    Returns:
        SyncManager: Менеджер синхронизации
    """
    manager = SyncManager(project_root)
    manager.start(callback)
    return manager


# ================================================================
# ТЕСТ
# ================================================================

if __name__ == "__main__":
    import sys
    import time
    from analitik_core.database import init_db

    def on_event(event_type: str, path: str, data: Any):
        """Обработчик событий синхронизации."""
        if event_type == 'started':
            print(f"🔄 Синхронизация запущена для: {path}")
        elif event_type == 'modified':
            print(f"📝 Изменён: {path} ({data.get('file', '')})")
        elif event_type == 'created':
            print(f"📄 Создан: {path} ({data.get('file', '')})")
        elif event_type == 'deleted':
            print(f"🗑️ Удалён: {path} ({data.get('file', '')})")
        elif event_type == 'error':
            print(f"❌ Ошибка: {path} — {data}")
        elif event_type == 'stopped':
            print(f"⏹️ Синхронизация остановлена: {path}")

    print("=" * 60)
    print("🧪 ТЕСТ СИНХРОНИЗАЦИИ")
    print("=" * 60)

    if not init_db():
        print("❌ Не удалось подключиться к БД")
        sys.exit(1)

    project_root = "/home/sergey/Documents/configurate"

    print(f"\n📂 Проект: {project_root}")
    print("⏳ Запуск синхронизации...")

    manager = sync_project(project_root, on_event)

    try:
        print("\n✅ Синхронизация запущена. Нажмите Ctrl+C для остановки.")
        print(f"📊 Статистика: {manager.get_stats()}")

        # Мониторинг в реальном времени
        while True:
            time.sleep(5)
            stats = manager.get_stats()
            if any(stats.values()):
                print(f"📊 Статистика: {stats}")

    except KeyboardInterrupt:
        print("\n⏹️ Остановка синхронизации...")
        manager.stop()
        print("✅ Синхронизация остановлена")