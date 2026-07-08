# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_gateway/gateway.py
"""
Файловый шлюз Аналитика Моцарт.
Материализует активные версии файлов из БД во временную директорию для работы IDE.
Версия: 2.0 — для единой таблицы сущностей
"""

import os
import shutil
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from pathlib import Path

from analitik_core.database import get_db, get_session
from analitik_core.models import Entity, EntityType


class GatewayManager:
    """
    Управляет временной рабочей директорией.
    Материализует код из БД в файлы на диске.
    """

    def __init__(self, project_root: str, temp_dir: Optional[str] = None, db_session=None):
        self.project_root = os.path.abspath(project_root)
        self.db_session = db_session or get_session()
        self.db = get_db()

        # По умолчанию используем папку .mozart_work рядом с проектом
        self.temp_dir = temp_dir or os.path.join(project_root, '.mozart_work')

        # Кэш для быстрого доступа к сущностям
        self._entity_cache = {}
        self._file_cache = {}

        # Статистика
        self.stats = {
            'files_created': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'errors': 0
        }

    # ================================================================
    # ПОДГОТОВКА РАБОЧЕГО ПРОСТРАНСТВА
    # ================================================================

    def prepare_workspace(self, view_time: Optional[datetime] = None) -> bool:
        """
        Очищает временную папку и выгружает туда актуальные файлы из БД.
        """
        dt = view_time or datetime.now()

        # Очищаем кэш
        self._entity_cache = {}
        self._file_cache = {}

        # 1. Очищаем старую папку
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"📂 Подготовка рабочего пространства в: {self.temp_dir}")

        # 2. Получаем все активные файлы на момент времени
        active_files = self._get_active_files(dt)

        if not active_files:
            print("⚠️ В базе нет активных файлов.")
            return False

        # 3. Выгружаем файлы
        success_count = 0
        for file_entity in active_files:
            try:
                # Собираем содержимое файла
                content = self._assemble_file_content(file_entity, dt)

                if content is None:
                    continue

                # Вычисляем относительный путь от корня проекта
                full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None
                if not full_path:
                    continue

                rel_path = os.path.relpath(full_path, self.project_root)
                target_path = os.path.join(self.temp_dir, rel_path)

                # Создаём директории
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # Записываем файл
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                success_count += 1
                self.stats['files_created'] += 1

            except Exception as e:
                print(f"❌ Ошибка выгрузки {file_entity.c_name}: {e}")
                self.stats['errors'] += 1

        print(f"✅ Выгружено {success_count} файлов в рабочее пространство.")
        return True

    def _get_active_files(self, dt: datetime) -> List[Entity]:
        """Получает все активные файлы на момент времени."""
        return self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).all()

    # ================================================================
    # СБОРКА ФАЙЛА ИЗ СУЩНОСТЕЙ
    # ================================================================

    def _assemble_file_content(self, file_entity: Entity, dt: datetime) -> Optional[str]:
        """
        Собирает содержимое файла из всех частей.
        """
        lines = []
        file_id = file_entity.id

        # 1. Заголовок файла (header)
        headers = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.HEADER,
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).first()

        if headers and headers.t_blobskript:
            lines.append(f'"""\n{headers.t_blobskript}\n"""')
            lines.append('')

        # 2. Импорты
        imports = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.IMPORT,
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).order_by(Entity.n_order).all()

        for imp in imports:
            lines.append(imp.t_blobskript or imp.c_name)
        if imports:
            lines.append('')

        # 3. Глобальные переменные
        globals_ = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.GLOBAL_VARIABLE,
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).order_by(Entity.n_order).all()

        for var in globals_:
            v_type = var.j_data.get('var_type', 'Any') if var.j_data else 'Any'
            v_value = var.j_data.get('var_value', '...') if var.j_data else '...'
            is_annotated = var.j_data.get('is_annotated', False) if var.j_data else False

            if is_annotated:
                lines.append(f"{var.c_name}: {v_type} = {v_value}")
            else:
                lines.append(f"{var.c_name} = {v_value}")
        if globals_:
            lines.append('')

        # 4. Процедуры
        procedures = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROCEDURE,
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).order_by(Entity.n_order).all()

        for proc in procedures:
            if proc.t_blobskript:
                lines.append(proc.t_blobskript)
                lines.append('')

        # 5. Классы
        classes = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.CLASS,
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).order_by(Entity.n_order).all()

        for cls in classes:
            # Заголовок класса
            if cls.t_blobskript:
                lines.append(cls.t_blobskript)
            else:
                bases = cls.j_data.get('bases', []) if cls.j_data else []
                lines.append(f"class {cls.c_name}({', '.join(bases)}):")

            # Докстринг класса
            if cls.m_comment:
                lines.append(f'    """\n    {cls.m_comment}\n    """')

            # Переменные класса
            class_vars = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.CLASS_VARIABLE,
                Entity.parent_id == cls.id,
                Entity.is_active == True,
                Entity.dt_start <= dt,
                (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
            ).order_by(Entity.n_order).all()

            for var in class_vars:
                v_type = var.j_data.get('var_type', 'Any') if var.j_data else 'Any'
                v_value = var.j_data.get('var_value', '...') if var.j_data else '...'
                lines.append(f"    {var.c_name}: {v_type} = {v_value}")

            # Свойства
            props = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.PROPERTY,
                Entity.parent_id == cls.id,
                Entity.is_active == True,
                Entity.dt_start <= dt,
                (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
            ).order_by(Entity.n_order).all()

            for prop in props:
                if prop.t_blobskript:
                    code_lines = prop.t_blobskript.split('\n')
                    for code_line in code_lines:
                        lines.append(f"    {code_line}")

            # Методы класса
            methods = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.METHOD,
                Entity.parent_id == cls.id,
                Entity.is_active == True,
                Entity.dt_start <= dt,
                (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
            ).order_by(Entity.n_order).all()

            for method in methods:
                if method.t_blobskript:
                    code_lines = method.t_blobskript.split('\n')
                    for code_line in code_lines:
                        lines.append(f"    {code_line}")
                    lines.append('')

            lines.append('')

        return '\n'.join(lines)

    # ================================================================
    # СИНХРОНИЗАЦИЯ ИЗМЕНЕНИЙ ИЗ ВРЕМЕННОЙ ПАПКИ В БД
    # ================================================================

    def sync_from_workspace(self, view_time: Optional[datetime] = None) -> Dict[str, int]:
        """
        Синхронизирует изменения из временной папки в БД.
        Обновляет только изменённые сущности.
        """
        dt = view_time or datetime.now()

        self.stats = {
            'files_created': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'entities_updated': 0,
            'errors': 0
        }

        if not os.path.exists(self.temp_dir):
            print("⚠️ Временная папка не существует")
            return self.stats

        print(f"🔄 Синхронизация из {self.temp_dir} в БД...")

        # Проходим по всем файлам во временной папке
        for root, dirs, files in os.walk(self.temp_dir):
            for filename in files:
                if not filename.endswith('.py'):
                    continue

                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.temp_dir)
                full_path = os.path.join(self.project_root, rel_path)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()

                    # Находим файл в БД
                    file_entity = self.db_session.query(Entity).filter(
                        Entity.type_id == EntityType.FILE,
                        Entity.j_data.contains({"full_path": full_path}),
                        Entity.is_active == True
                    ).first()

                    if file_entity:
                        # Проверяем, изменился ли файл
                        current_content = self._assemble_file_content(file_entity, dt)

                        if current_content != new_content:
                            # Файл изменился — обновляем
                            self._update_file_from_content(file_entity, new_content, dt)
                            self.stats['files_updated'] += 1
                    else:
                        # Новый файл — создаём
                        self._create_file_from_content(full_path, new_content, dt)
                        self.stats['files_created'] += 1

                except Exception as e:
                    print(f"❌ Ошибка синхронизации {filename}: {e}")
                    self.stats['errors'] += 1

        # Закрываем файлы, которые были удалены из временной папки
        self._cleanup_deleted_files(dt)

        self.db_session.commit()

        print(f"✅ Синхронизация завершена")
        return self.stats

    def _update_file_from_content(self, file_entity: Entity, new_content: str, dt: datetime):
        """
        Обновляет файл в БД на основе нового содержимого.
        """
        from analitik_core.parser import PythonParser

        parser = PythonParser()
        full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None

        if not full_path:
            return

        # Парсим новое содержимое
        parse_result = parser.parse_file(full_path, new_content)

        # Закрываем старую версию файла
        file_entity.is_active = False
        file_entity.dt_end = datetime.now()

        # Создаём новую версию файла
        new_file = Entity(
            type_id=EntityType.FILE,
            c_name=file_entity.c_name,
            parent_id=file_entity.parent_id,
            j_data=file_entity.j_data.copy() if file_entity.j_data else {},
            n_old_version=file_entity.id
        )
        new_file.j_data['size_bytes'] = len(new_content.encode('utf-8'))
        self.db_session.add(new_file)
        self.db_session.flush()

        # Обновляем структуру файла
        self._update_file_structure(new_file.id, parse_result, dt)

        self.stats['entities_updated'] += 1

    def _create_file_from_content(self, full_path: str, content: str, dt: datetime):
        """
        Создаёт новый файл в БД на основе содержимого.
        """
        from analitik_core.parser import PythonParser

        parser = PythonParser()
        parse_result = parser.parse_file(full_path, content)

        # Находим или создаём родительский каталог
        dir_path = os.path.dirname(full_path)
        parent_entity = self._get_or_create_directory(dir_path, dt)

        # Создаём файл
        file_entity = Entity(
            type_id=EntityType.FILE,
            c_name=os.path.basename(full_path),
            parent_id=parent_entity.id if parent_entity else None,
            j_data={
                "full_path": full_path,
                "extension": ".py",
                "is_python": True,
                "size_bytes": len(content.encode('utf-8'))
            }
        )
        self.db_session.add(file_entity)
        self.db_session.flush()

        # Загружаем структуру
        self._update_file_structure(file_entity.id, parse_result, dt)

        self.stats['entities_updated'] += 1

    def _update_file_structure(self, file_id: str, parse_result: Dict, dt: datetime):
        """
        Обновляет структуру файла на основе результата парсинга.
        """
        # Удаляем старые дочерние сущности (кроме активных версий)
        self.db_session.query(Entity).filter(
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).update({'is_active': False, 'dt_end': datetime.now()})

        # 1. Заголовок
        header = parse_result.get('header', '')
        if header:
            header_entity = Entity(
                type_id=EntityType.HEADER,
                c_name=f"# Заголовок: {os.path.basename(parse_result.get('file_path', ''))}",
                parent_id=file_id,
                t_blobskript=header,
                m_comment="Заголовочный комментарий файла"
            )
            self.db_session.add(header_entity)

        # 2. Импорты
        for imp in parse_result.get('imports', []):
            imp_entity = Entity(
                type_id=EntityType.IMPORT,
                c_name=imp.get('name', imp.get('module_path', 'import')),
                parent_id=file_id,
                t_blobskript=imp.get('name', ''),
                n_order=imp.get('position', 0),
                j_data={
                    "import_type": "from_import" if imp.get('imported_names') else "import",
                    "module_path": imp.get('module_path', ''),
                    "alias": imp.get('alias'),
                    "imported_names": imp.get('imported_names', [])
                }
            )
            self.db_session.add(imp_entity)

        # 3. Глобальные переменные
        for var in parse_result.get('global_variables', []):
            var_entity = Entity(
                type_id=EntityType.GLOBAL_VARIABLE,
                c_name=var['name'],
                parent_id=file_id,
                n_order=var.get('position', 0),
                j_data={
                    "var_type": var.get('type'),
                    "var_value": var.get('value'),
                    "is_constant": var.get('is_constant', False),
                    "is_annotated": var.get('is_annotated', False)
                },
                m_comment=var.get('comment', '')
            )
            self.db_session.add(var_entity)

        # 4. Процедуры
        for proc in parse_result.get('procedures', []):
            proc_entity = Entity(
                type_id=EntityType.PROCEDURE,
                c_name=proc['name'],
                parent_id=file_id,
                t_blobskript=proc.get('code', ''),
                n_order=proc.get('position', 0),
                j_data={
                    "is_async": proc.get('is_async', False),
                    "is_generator": proc.get('is_generator', False),
                    "return_type": proc.get('return_type')
                },
                m_comment=proc.get('docstring', '') or proc.get('description', '')
            )
            self.db_session.add(proc_entity)
            self.db_session.flush()

            # Параметры процедуры
            for param in proc.get('params', []):
                param_entity = Entity(
                    type_id=EntityType.PARAMETER,
                    c_name=param['name'],
                    parent_id=proc_entity.id,
                    n_order=param.get('position', 0),
                    j_data={
                        "param_type": param.get('type'),
                        "default_value": param.get('default'),
                        "is_required": param.get('is_required', True)
                    }
                )
                self.db_session.add(param_entity)

            # Локальные переменные
            for local in proc.get('locals', []):
                local_entity = Entity(
                    type_id=EntityType.LOCAL_VARIABLE,
                    c_name=local['name'],
                    parent_id=proc_entity.id,
                    n_order=local.get('position', 0),
                    j_data={"var_type": local.get('type')},
                    m_comment=local.get('comment', '')
                )
                self.db_session.add(local_entity)

            # Вызовы
            for call in proc.get('calls', []):
                from analitik_core.models import Call
                call_obj = Call(
                    caller_entity_id=proc_entity.id,
                    callee_name=call['callee_name'],
                    callee_type=call.get('callee_type', 'unknown'),
                    line_number=call.get('line_number', 0)
                )
                self.db_session.add(call_obj)

        # 5. Классы
        for cls in parse_result.get('classes', []):
            cls_entity = Entity(
                type_id=EntityType.CLASS,
                c_name=cls['name'],
                parent_id=file_id,
                t_blobskript=f"class {cls['name']}({', '.join(cls.get('bases', []))}):",
                n_order=cls.get('position', 0),
                j_data={
                    "bases": cls.get('bases', []),
                    "is_dataclass": cls.get('is_dataclass', False)
                },
                m_comment=cls.get('docstring', '') or cls.get('description', '')
            )
            self.db_session.add(cls_entity)
            self.db_session.flush()

            # Переменные класса
            for var in cls.get('class_vars', []):
                var_entity = Entity(
                    type_id=EntityType.CLASS_VARIABLE,
                    c_name=var['name'],
                    parent_id=cls_entity.id,
                    n_order=var.get('position', 0),
                    j_data={
                        "var_type": var.get('type'),
                        "var_value": var.get('value'),
                        "is_constant": var.get('is_constant', False)
                    },
                    m_comment=var.get('comment', '')
                )
                self.db_session.add(var_entity)

            # Свойства
            for prop in cls.get('properties', []):
                prop_entity = Entity(
                    type_id=EntityType.PROPERTY,
                    c_name=prop['name'],
                    parent_id=cls_entity.id,
                    t_blobskript=prop.get('getter_code', ''),
                    n_order=prop.get('position', 0),
                    j_data={
                        "prop_type": prop.get('type'),
                        "is_readonly": prop.get('is_readonly', True)
                    }
                )
                self.db_session.add(prop_entity)

            # Методы
            for method in cls.get('methods', []):
                method_entity = Entity(
                    type_id=EntityType.METHOD,
                    c_name=method['name'],
                    parent_id=cls_entity.id,
                    t_blobskript=method.get('code', ''),
                    n_order=method.get('position', 0),
                    j_data={
                        "method_type": method.get('method_type', 'instance'),
                        "is_async": method.get('is_async', False),
                        "is_generator": method.get('is_generator', False),
                        "return_type": method.get('return_type')
                    },
                    m_comment=method.get('docstring', '')
                )
                self.db_session.add(method_entity)
                self.db_session.flush()

                # Параметры метода
                for param in method.get('params', []):
                    param_entity = Entity(
                        type_id=EntityType.PARAMETER,
                        c_name=param['name'],
                        parent_id=method_entity.id,
                        n_order=param.get('position', 0),
                        j_data={
                            "param_type": param.get('type'),
                            "default_value": param.get('default'),
                            "is_required": param.get('is_required', True)
                        }
                    )
                    self.db_session.add(param_entity)

                # Локальные переменные метода
                for local in method.get('locals', []):
                    local_entity = Entity(
                        type_id=EntityType.LOCAL_VARIABLE,
                        c_name=local['name'],
                        parent_id=method_entity.id,
                        n_order=local.get('position', 0),
                        j_data={"var_type": local.get('type')},
                        m_comment=local.get('comment', '')
                    )
                    self.db_session.add(local_entity)

                # Вызовы из метода
                for call in method.get('calls', []):
                    from analitik_core.models import Call
                    call_obj = Call(
                        caller_entity_id=method_entity.id,
                        callee_name=call['callee_name'],
                        callee_type=call.get('callee_type', 'unknown'),
                        line_number=call.get('line_number', 0)
                    )
                    self.db_session.add(call_obj)

    def _get_or_create_directory(self, dir_path: str, dt: datetime) -> Optional[Entity]:
        """
        Получает или создаёт каталог в БД.
        """
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
            parent_entity = self._get_or_create_directory(parent_path, dt)

        entity = Entity(
            type_id=EntityType.DIRECTORY,
            c_name=os.path.basename(dir_path),
            parent_id=parent_entity.id if parent_entity else None,
            j_data={"full_path": dir_path}
        )
        self.db_session.add(entity)
        self.db_session.flush()

        return entity

    def _cleanup_deleted_files(self, dt: datetime):
        """
        Закрывает файлы, которые были удалены из временной папки.
        """
        active_files = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).all()

        for file_entity in active_files:
            full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None
            if not full_path:
                continue

            rel_path = os.path.relpath(full_path, self.project_root)
            temp_path = os.path.join(self.temp_dir, rel_path)

            if not os.path.exists(temp_path):
                file_entity.is_active = False
                file_entity.dt_end = datetime.now()
                self.stats['files_deleted'] += 1

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    def get_work_path(self) -> str:
        """Возвращает путь к временной рабочей директории."""
        return self.temp_dir

    def get_file_from_workspace(self, rel_path: str) -> Optional[str]:
        """
        Возвращает содержимое файла из рабочей директории.
        """
        full_path = os.path.join(self.temp_dir, rel_path)
        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def write_file_to_workspace(self, rel_path: str, content: str) -> bool:
        """
        Записывает файл в рабочую директорию.
        """
        full_path = os.path.join(self.temp_dir, rel_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def delete_file_from_workspace(self, rel_path: str) -> bool:
        """
        Удаляет файл из рабочей директории.
        """
        full_path = os.path.join(self.temp_dir, rel_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            return True
        except Exception:
            return False

    def get_workspace_files(self) -> List[str]:
        """
        Возвращает список всех файлов в рабочей директории.
        """
        files = []
        for root, dirs, filenames in os.walk(self.temp_dir):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.temp_dir)
                files.append(rel_path)
        return files

    # ================================================================
    # СТАТИСТИКА
    # ================================================================

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику последней операции."""
        return self.stats.copy()

    def reset_stats(self):
        """Сбрасывает статистику."""
        self.stats = {
            'files_created': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'entities_updated': 0,
            'errors': 0
        }

    def print_stats(self):
        """Выводит статистику в консоль."""
        print("\n📊 СТАТИСТИКА ГАТЕЙВЭЯ:")
        print(f"  📄 Создано файлов: {self.stats['files_created']}")
        print(f"  📝 Обновлено файлов: {self.stats['files_updated']}")
        print(f"  🗑️ Удалено файлов: {self.stats['files_deleted']}")
        print(f"  🔧 Обновлено сущностей: {self.stats['entities_updated']}")
        if self.stats['errors'] > 0:
            print(f"  ❌ Ошибок: {self.stats['errors']}")


# ================================================================
# УТИЛИТА ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def prepare_workspace(project_root: str, view_time: Optional[datetime] = None) -> bool:
    """
    Быстрая подготовка рабочего пространства.
    """
    gateway = GatewayManager(project_root)
    return gateway.prepare_workspace(view_time)


def sync_workspace(project_root: str, view_time: Optional[datetime] = None) -> Dict[str, int]:
    """
    Быстрая синхронизация из рабочей директории в БД.
    """
    gateway = GatewayManager(project_root)
    return gateway.sync_from_workspace(view_time)


# ================================================================
# ТЕСТ
# ================================================================

if __name__ == "__main__":
    import sys
    from analitik_core.database import init_db

    print("=" * 60)
    print("🧪 ТЕСТ ФАЙЛОВОГО ШЛЮЗА")
    print("=" * 60)

    if not init_db():
        print("❌ Не удалось подключиться к БД")
        sys.exit(1)

    project_root = "/home/sergey/Documents/configurate"

    # Подготовка рабочего пространства
    gateway = GatewayManager(project_root)
    success = gateway.prepare_workspace()

    if success:
        print(f"✅ Рабочее пространство: {gateway.get_work_path()}")
        gateway.print_stats()

        # Выводим список файлов
        files = gateway.get_workspace_files()
        print(f"\n📄 Файлов в рабочей директории: {len(files)}")
        for f in files[:10]:
            print(f"  - {f}")
        if len(files) > 10:
            print(f"  ... и ещё {len(files) - 10} файлов")
    else:
        print("❌ Не удалось подготовить рабочее пространство")