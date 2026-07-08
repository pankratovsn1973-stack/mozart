# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_scanner/loader.py
"""
Загрузчик данных в БД для Аналитика Моцарт.
Версия: 4.3 — только Entity (единая таблица)
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from analitik_core.database import get_db, get_session
from analitik_core.models import Entity, EntityType, Call
from analitik_core.parser import PythonParser
from analitik_core.description_loader import DescriptionLoader
from analitik_scanner.scanner import ProjectScanner


class DataLoader:
    """Загрузчик данных в БД."""

    def __init__(self, project_root: str, db_session: Session = None):
        self.project_root = os.path.abspath(project_root)
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.scanner = ProjectScanner(project_root, self.db_session)
        self.parser = PythonParser()
        self.description_loader = DescriptionLoader()

        self._entity_cache = {}
        self._file_cache = {}

        self.stats = {
            'directories': 0,
            'files': 0,
            'python_files': 0,
            'classes': 0,
            'methods': 0,
            'procedures': 0,
            'variables': 0,
            'imports': 0,
            'calls': 0,
            'headers': 0,
            'properties': 0,
            'parameters': 0,
            'local_variables': 0,
            'class_variables': 0,
            'global_variables': 0,
            'errors': 0,
            'enriched': 0,
            'skipped': 0
        }

    def load(self) -> Dict[str, int]:
        """Запускает полную загрузку данных в БД."""
        print("🚀 ЗАГРУЗКА ДАННЫХ В БД")
        print("=" * 60)

        # 1. Сканируем проект
        print("\n📁 ШАГ 1: Сканирование проекта...")
        scan_stats = self.scanner.scan()
        self.stats['directories'] = scan_stats.get('directories', 0)
        self.stats['files'] = scan_stats.get('files', 0)
        self.stats['python_files'] = scan_stats.get('python_files', 0)
        self.stats['errors'] += scan_stats.get('errors', 0)
        self.stats['skipped'] += scan_stats.get('skipped', 0)

        self._entity_cache = {}
        self._file_cache = {}

        print("\n📄 ШАГ 2: Парсинг Python файлов с обогащением...")
        self._parse_all_python_files()

        print("\n🧹 ШАГ 3: Очистка удалённых файлов...")
        self._cleanup_deleted_files()

        self._update_stats()

        self.db_session.commit()

        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ЗАГРУЗКИ:")
        print(f"  📁 Каталогов: {self.stats['directories']}")
        print(f"  📄 Файлов всего: {self.stats['files']}")
        print(f"  🐍 Python файлов: {self.stats['python_files']}")
        print(f"  📦 Классов: {self.stats['classes']}")
        print(f"  🔧 Методов: {self.stats['methods']}")
        print(f"  ⚡ Процедур/функций: {self.stats['procedures']}")
        print(f"  🔤 Переменных (всего): {self.stats['variables']}")
        print(f"     - Глобальные: {self.stats['global_variables']}")
        print(f"     - Локальные: {self.stats['local_variables']}")
        print(f"     - Классовые: {self.stats['class_variables']}")
        print(f"  📥 Импортов: {self.stats['imports']}")
        print(f"  📝 Заголовков: {self.stats['headers']}")
        print(f"  🔒 Свойств: {self.stats['properties']}")
        print(f"  📌 Параметров: {self.stats['parameters']}")
        print(f"  📞 Вызовов: {self.stats['calls']}")
        print(f"  💡 Обогащено описаниями: {self.stats['enriched']}")
        if self.stats['errors'] > 0:
            print(f"  ❌ Ошибок: {self.stats['errors']}")
        if self.stats['skipped'] > 0:
            print(f"  ⏭️ Пропущено: {self.stats['skipped']}")

        return self.stats

    # ================================================================
    # ПАРСИНГ PYTHON ФАЙЛОВ
    # ================================================================

    def _parse_all_python_files(self):
        """Парсит все активные Python файлы."""
        all_files = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).all()

        python_files = [f for f in all_files if f.j_data and f.j_data.get('is_python', False)]

        total = len(python_files)
        print(f"  Найдено Python файлов: {total}")

        for idx, file_entity in enumerate(python_files):
            if (idx + 1) % 10 == 0:
                print(f"    Обработано: {idx + 1}/{total}")

            try:
                full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None
                if not full_path or not os.path.exists(full_path):
                    continue

                self._file_cache[full_path] = file_entity.id

                # 1. ЧИТАЕМ ФАЙЛ
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 2. ДОБАВЛЯЕМ ОПИСАНИЕ
                enriched_content = self._add_description_to_file(full_path, content)

                # 3. СОХРАНЯЕМ ПОЛНЫЙ ТЕКСТ
                file_entity.t_full_text = enriched_content
                file_entity.m_comment = self._get_file_description(full_path)
                self.stats['enriched'] += 1

                # 4. ПАРСИМ
                parse_result = self.parser.parse_file(full_path, content)

                if parse_result.get('error'):
                    print(f"    ⚠️ Ошибка парсинга {file_entity.c_name}: {parse_result['error']}")
                    self.stats['errors'] += 1
                    continue

                # Закрываем старые дочерние сущности
                self.db_session.query(Entity).filter(
                    Entity.parent_id == file_entity.id,
                    Entity.is_active == True
                ).update({'is_active': False, 'dt_end': datetime.now()})

                # Загружаем атомарные части
                self._load_imports(file_entity.id, parse_result.get('imports', []))
                self._load_global_variables(file_entity.id, parse_result.get('global_variables', []))
                self._load_procedures(file_entity.id, parse_result.get('procedures', []))
                self._load_classes(file_entity.id, parse_result.get('classes', []))

                if (idx + 1) % 5 == 0:
                    self.db_session.flush()

            except Exception as e:
                print(f"    ❌ Ошибка обработки {file_entity.c_name}: {e}")
                import traceback
                traceback.print_exc()
                self.stats['errors'] += 1
                continue

        self.db_session.commit()

    # ================================================================
    # ДОБАВЛЕНИЕ ОПИСАНИЯ
    # ================================================================

    def _add_description_to_file(self, file_path: str, content: str) -> str:
        """Добавляет описание из документации в начало файла."""
        desc = self._get_file_description(file_path)

        if not desc:
            return content

        lines = content.split('\n')

        insert_pos = 0
        in_docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith('#!') or 'coding:' in stripped:
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().endswith('"""') or lines[j].strip().endswith("'''"):
                        insert_pos = j + 1
                        break
                break

            if stripped and not stripped.startswith('#'):
                insert_pos = i
                break

        if insert_pos == 0:
            return f'# {desc}\n\n{content}'
        else:
            lines.insert(insert_pos, '')
            lines.insert(insert_pos + 1, f'# {desc}')
            return '\n'.join(lines)

    def _get_file_description(self, file_path: str) -> str:
        """Возвращает описание файла из документации."""
        desc = self.description_loader.get_file_description(file_path)
        return desc.get('description', '')

    # ================================================================
    # ИЗВЛЕЧЕНИЕ БЛОКА ТЕКСТА
    # ================================================================

    def _get_block_text(self, full_text: str, start_line: int) -> Dict[str, Any]:
        """Извлекает блок текста по отступам."""
        lines = full_text.split('\n')
        if start_line < 1 or start_line > len(lines):
            return {'text': '', 'end_line': start_line}

        start_idx = start_line - 1
        first_line = lines[start_idx]

        indent = len(first_line) - len(first_line.lstrip())

        end_idx = start_idx
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                end_idx = i
                continue
            cur_indent = len(line) - len(line.lstrip())
            if cur_indent <= indent:
                break
            end_idx = i

        block_text = '\n'.join(lines[start_idx:end_idx + 1])

        return {
            'text': block_text,
            'end_line': end_idx + 1
        }

    # ================================================================
    # ЗАГРУЗКА ИМПОРТОВ
    # ================================================================

    def _load_imports(self, file_id: str, imports: List[Dict]):
        """Загружает импорты."""
        full_text = self.db_session.query(Entity).filter(Entity.id == file_id).first().t_full_text
        lines = full_text.split('\n')

        for imp in imports:
            line_idx = imp.get('position', 1) - 1
            line = lines[line_idx] if 0 <= line_idx < len(lines) else imp.get('text', '')

            imp_entity = self._create_entity(
                type_id=EntityType.IMPORT,
                name=line.strip(),
                parent_id=file_id,
                blob=line,
                order=imp.get('position', 0),
                comment=imp.get('comment', '')
            )
            imp_entity.t_full_text = line
            self.stats['imports'] += 1

    # ================================================================
    # ЗАГРУЗКА ГЛОБАЛЬНЫХ ПЕРЕМЕННЫХ
    # ================================================================

    def _load_global_variables(self, file_id: str, variables: List[Dict]):
        """Загружает глобальные переменные."""
        full_text = self.db_session.query(Entity).filter(Entity.id == file_id).first().t_full_text
        lines = full_text.split('\n')

        for var in variables:
            line_idx = var.get('position', 1) - 1
            line = lines[line_idx] if 0 <= line_idx < len(lines) else var.get('text', '')

            var_entity = self._create_entity(
                type_id=EntityType.GLOBAL_VARIABLE,
                name=var['name'],
                parent_id=file_id,
                blob=line,
                order=var.get('position', 0),
                j_data={
                    "value": var.get('value'),
                    "type": var.get('type'),
                    "is_constant": var.get('is_constant', False),
                    "is_annotated": var.get('is_annotated', False)
                },
                comment=var.get('comment', '')
            )
            var_entity.t_full_text = line
            self.stats['global_variables'] += 1
            self.stats['variables'] += 1

    # ================================================================
    # ЗАГРУЗКА ПРОЦЕДУР
    # ================================================================

    def _load_procedures(self, file_id: str, procedures: List[Dict]):
        """Загружает процедуры."""
        if not procedures:
            return

        full_text = self.db_session.query(Entity).filter(Entity.id == file_id).first().t_full_text
        lines = full_text.split('\n')

        for proc in procedures:
            if not proc.get('name'):
                continue

            proc_text = proc.get('text', '')
            if not proc_text:
                start = proc.get('position', 1) - 1
                end = proc.get('end_line', start + 1) - 1
                proc_text = '\n'.join(lines[start:end]) if start < len(lines) else ''

            if not proc_text:
                continue

            # Сохраняем процедуру
            proc_entity = self._create_entity(
                type_id=EntityType.PROCEDURE,
                name=proc['name'],
                parent_id=file_id,
                blob=proc_text,
                order=proc.get('position', 0),
                j_data={
                    "is_async": proc.get('is_async', False),
                    "is_generator": proc.get('is_generator', False),
                    "return_type": proc.get('return_type'),
                    "decorators": proc.get('decorators', []),
                    "params": proc.get('params', [])
                },
                comment=proc.get('docstring', '') or proc.get('description', '')
            )
            proc_entity.t_full_text = proc_text
            self.stats['procedures'] += 1

            # Параметры
            for param in proc.get('params', []):
                self._create_entity(
                    type_id=EntityType.PARAMETER,
                    name=param.get('name', ''),
                    parent_id=proc_entity.id,
                    blob=f"{param.get('name', '')}: {param.get('type', 'Any')}",
                    order=0,
                    j_data={
                        "type": param.get('type'),
                        "default": param.get('default'),
                        "is_required": param.get('is_required', True)
                    }
                )
                self.stats['parameters'] += 1

            # Вызовы
            for call in proc.get('calls', []):
                self._create_call(
                    proc_entity.id,
                    call.get('callee_name', ''),
                    call.get('callee_type', 'unknown'),
                    call.get('line_number', 0)
                )
                self.stats['calls'] += 1

    # ================================================================
    # ЗАГРУЗКА КЛАССОВ
    # ================================================================

    def _load_classes(self, file_id: str, classes: List[Dict]):
        """Загружает классы."""
        if not classes:
            return

        full_text = self.db_session.query(Entity).filter(Entity.id == file_id).first().t_full_text
        lines = full_text.split('\n')

        for cls in classes:
            if not cls.get('name'):
                continue

            cls_text = cls.get('text', '')
            if not cls_text:
                start = cls.get('position', 1) - 1
                end = cls.get('end_line', start + 1) - 1
                cls_text = '\n'.join(lines[start:end]) if start < len(lines) else ''

            if not cls_text:
                continue

            header = cls.get('header', '')
            if not header:
                header = lines[cls.get('position', 1) - 1] if cls.get('position', 1) <= len(lines) else f"class {cls['name']}:"

            # Сохраняем класс
            cls_entity = self._create_entity(
                type_id=EntityType.CLASS,
                name=cls['name'],
                parent_id=file_id,
                blob=header,
                order=cls.get('position', 0),
                j_data={
                    "bases": cls.get('bases', []),
                    "is_dataclass": cls.get('is_dataclass', False),
                    "full_text": cls_text,
                    "methods": cls.get('methods', [])
                },
                comment=cls.get('docstring', '') or cls.get('description', '')
            )
            cls_entity.t_full_text = cls_text
            self.stats['classes'] += 1

            # Переменные класса
            for var in cls.get('class_variables', []):
                line_idx = var.get('position', 1) - 1
                line = lines[line_idx] if 0 <= line_idx < len(lines) else var.get('text', '')

                self._create_entity(
                    type_id=EntityType.CLASS_VARIABLE,
                    name=var['name'],
                    parent_id=cls_entity.id,
                    blob=line,
                    order=var.get('position', 0),
                    j_data={
                        "value": var.get('value'),
                        "type": var.get('type'),
                        "is_annotated": var.get('is_annotated', False)
                    },
                    comment=var.get('comment', '')
                )
                self.stats['class_variables'] += 1
                self.stats['variables'] += 1

            # Свойства
            for prop in cls.get('properties', []):
                prop_text = prop.get('text', '')
                if not prop_text:
                    start_p = prop.get('position', 1) - 1
                    end_p = prop.get('end_line', start_p + 1) - 1
                    prop_text = '\n'.join(lines[start_p:end_p]) if start_p < len(lines) else ''

                self._create_entity(
                    type_id=EntityType.PROPERTY,
                    name=prop['name'],
                    parent_id=cls_entity.id,
                    blob=prop_text,
                    order=prop.get('position', 0),
                    j_data={
                        "return_type": prop.get('return_type', 'Any'),
                        "is_readonly": prop.get('is_readonly', True)
                    },
                    comment=prop.get('comment', '')
                )
                self.stats['properties'] += 1

            # Методы
            for method in cls.get('methods', []):
                method_text = method.get('text', '')
                if not method_text:
                    start_m = method.get('position', 1) - 1
                    end_m = method.get('end_line', start_m + 1) - 1
                    method_text = '\n'.join(lines[start_m:end_m]) if start_m < len(lines) else ''

                if not method_text:
                    continue

                method_entity = self._create_entity(
                    type_id=EntityType.METHOD,
                    name=method['name'],
                    parent_id=cls_entity.id,
                    blob=method_text,
                    order=method.get('position', 0),
                    j_data={
                        "method_type": method.get('method_type', 'instance'),
                        "is_async": method.get('is_async', False),
                        "is_generator": method.get('is_generator', False),
                        "return_type": method.get('return_type'),
                        "decorators": method.get('decorators', []),
                        "params": method.get('params', [])
                    },
                    comment=method.get('docstring', '')
                )
                method_entity.t_full_text = method_text
                self.stats['methods'] += 1

                # Параметры метода
                for param in method.get('params', []):
                    self._create_entity(
                        type_id=EntityType.PARAMETER,
                        name=param.get('name', ''),
                        parent_id=method_entity.id,
                        blob=f"{param.get('name', '')}: {param.get('type', 'Any')}",
                        order=0,
                        j_data={
                            "type": param.get('type'),
                            "default": param.get('default'),
                            "is_required": param.get('is_required', True)
                        }
                    )
                    self.stats['parameters'] += 1

                # Вызовы
                for call in method.get('calls', []):
                    self._create_call(
                        method_entity.id,
                        call.get('callee_name', ''),
                        call.get('callee_type', 'unknown'),
                        call.get('line_number', 0)
                    )
                    self.stats['calls'] += 1

    # ================================================================
    # РАБОТА С СУЩНОСТЯМИ
    # ================================================================

    def _create_entity(
            self,
            type_id: int,
            name: str,
            parent_id: Optional[str] = None,
            blob: Optional[str] = None,
            order: int = 0,
            j_data: Optional[Dict] = None,
            comment: Optional[str] = None,
            relise: Optional[str] = None
    ) -> Entity:
        entity = Entity(
            type_id=type_id,
            c_name=name,
            parent_id=parent_id,
            t_blobskript=blob,
            n_order=order,
            j_data=j_data or {},
            m_comment=comment,
            n_relise=relise
        )
        self.db_session.add(entity)
        self.db_session.flush()
        return entity

    def _create_call(self, caller_id: str, callee_name: str, callee_type: str, line_number: int):
        call = Call(
            caller_entity_id=caller_id,
            callee_name=callee_name,
            callee_type=callee_type,
            line_number=line_number
        )
        self.db_session.add(call)

    def _cleanup_deleted_files(self):
        active_files = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).all()

        closed_count = 0
        for file_entity in active_files:
            full_path = file_entity.j_data.get('full_path') if file_entity.j_data else None
            if full_path and not os.path.exists(full_path):
                file_entity.is_active = False
                file_entity.dt_end = datetime.now()
                closed_count += 1

        if closed_count > 0:
            print(f"    🗑️ Закрыто файлов (удалены с диска): {closed_count}")

    def _update_stats(self):
        self.stats['directories'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.is_active == True
        ).count()

        self.stats['files'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).count()

        all_files = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).all()
        self.stats['python_files'] = sum(1 for f in all_files if f.j_data and f.j_data.get('is_python', False))

        self.stats['classes'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.CLASS,
            Entity.is_active == True
        ).count()

        self.stats['methods'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.METHOD,
            Entity.is_active == True
        ).count()

        self.stats['procedures'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROCEDURE,
            Entity.is_active == True
        ).count()

        self.stats['imports'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.IMPORT,
            Entity.is_active == True
        ).count()

        self.stats['properties'] = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROPERTY,
            Entity.is_active == True
        ).count()

        self.stats['calls'] = self.db_session.query(Call).filter(
            Call.is_active == True
        ).count()


# ================================================================
# УТИЛИТА
# ================================================================

def load_project(project_root: str) -> Dict[str, int]:
    loader = DataLoader(project_root)
    return loader.load()