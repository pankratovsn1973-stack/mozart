# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_search/search.py
"""
Глобальный поиск по коду для Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
"""

import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy import text

from analitik_core.database import get_db, get_session
from analitik_core.models import Entity, EntityType


class CodeSearch:
    """Глобальный поиск по коду с учётом версионности."""

    def __init__(self, db_session=None, view_time: datetime = None):
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.view_time = view_time or datetime.now()

    # ================================================================
    # ОСНОВНОЙ ПОИСК
    # ================================================================

    def search(self, query: str, search_type: str = 'all') -> Dict[str, List]:
        """
        Выполняет поиск с учётом времени.

        Args:
            query: Поисковый запрос
            search_type: 'all', 'file', 'class', 'method', 'procedure', 'variable', 'import'

        Returns:
            Словарь с результатами по категориям
        """
        if not query or len(query) < 2:
            return {'error': 'Запрос должен содержать минимум 2 символа'}

        results = {
            'files': [],
            'directories': [],
            'classes': [],
            'methods': [],
            'procedures': [],
            'variables': [],
            'imports': [],
            'headers': [],
            'properties': [],
            'total': 0
        }

        dt = self.view_time or datetime.now()
        q_lower = query.lower()

        # Получаем все активные сущности на момент времени
        entities = self.db_session.query(Entity).filter(
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).all()

        # Поиск по типу
        type_map = {
            'file': EntityType.FILE,
            'class': EntityType.CLASS,
            'method': EntityType.METHOD,
            'procedure': EntityType.PROCEDURE,
            'variable': (EntityType.GLOBAL_VARIABLE, EntityType.LOCAL_VARIABLE, EntityType.CLASS_VARIABLE),
            'import': EntityType.IMPORT,
            'header': EntityType.HEADER,
            'property': EntityType.PROPERTY,
            'directory': EntityType.DIRECTORY
        }

        # Если указан конкретный тип — фильтруем
        if search_type in type_map:
            target_types = type_map[search_type]
            if isinstance(target_types, tuple):
                entities = [e for e in entities if e.type_id in target_types]
            else:
                entities = [e for e in entities if e.type_id == target_types]

        for entity in entities:
            # Проверяем совпадение
            match_info = self._check_match(entity, q_lower)

            if match_info:
                result_item = self._entity_to_result(entity, match_info)

                # Добавляем в соответствующую категорию
                type_id = entity.type_id
                if type_id == EntityType.FILE:
                    results['files'].append(result_item)
                elif type_id == EntityType.DIRECTORY:
                    results['directories'].append(result_item)
                elif type_id == EntityType.CLASS:
                    results['classes'].append(result_item)
                elif type_id == EntityType.METHOD:
                    results['methods'].append(result_item)
                elif type_id == EntityType.PROCEDURE:
                    results['procedures'].append(result_item)
                elif type_id in (EntityType.GLOBAL_VARIABLE, EntityType.LOCAL_VARIABLE, EntityType.CLASS_VARIABLE):
                    results['variables'].append(result_item)
                elif type_id == EntityType.IMPORT:
                    results['imports'].append(result_item)
                elif type_id == EntityType.HEADER:
                    results['headers'].append(result_item)
                elif type_id == EntityType.PROPERTY:
                    results['properties'].append(result_item)

        # Подсчитываем общее количество
        for key in ['files', 'directories', 'classes', 'methods', 'procedures',
                    'variables', 'imports', 'headers', 'properties']:
            results['total'] += len(results[key])

        return results

    # ================================================================
    # ПРОВЕРКА СОВПАДЕНИЙ
    # ================================================================

    def _check_match(self, entity: Entity, query: str) -> Optional[Dict]:
        """
        Проверяет, соответствует ли сущность запросу.
        Возвращает информацию о совпадении или None.
        """
        matches = []
        type_id = entity.type_id

        # 1. Поиск по имени
        if query in entity.c_name.lower():
            matches.append('имя')

        # 2. Поиск по комментарию
        if entity.m_comment and query in entity.m_comment.lower():
            matches.append('описание')

        # 3. Поиск по коду
        if entity.t_blobskript and query in entity.t_blobskript.lower():
            matches.append('код')

        # 4. Поиск по данным (j_data)
        if entity.j_data:
            j_data_str = str(entity.j_data).lower()
            if query in j_data_str:
                matches.append('данные')

        # 5. Специфичные проверки
        if type_id == EntityType.FILE:
            # Поиск по пути
            full_path = entity.j_data.get('full_path', '') if entity.j_data else ''
            if query in full_path.lower():
                matches.append('путь')

        elif type_id == EntityType.METHOD:
            # Поиск по типу метода
            method_type = entity.j_data.get('method_type', '') if entity.j_data else ''
            if query in method_type.lower():
                matches.append('тип метода')

        elif type_id == EntityType.IMPORT:
            # Поиск по модулю
            module_path = entity.j_data.get('module_path', '') if entity.j_data else ''
            if query in module_path.lower():
                matches.append('модуль')

        elif type_id in (EntityType.GLOBAL_VARIABLE, EntityType.LOCAL_VARIABLE, EntityType.CLASS_VARIABLE):
            # Поиск по типу переменной
            var_type = entity.j_data.get('var_type', '') if entity.j_data else ''
            if query in var_type.lower():
                matches.append('тип переменной')

        elif type_id == EntityType.PARAMETER:
            # Поиск по типу параметра
            param_type = entity.j_data.get('param_type', '') if entity.j_data else ''
            if query in param_type.lower():
                matches.append('тип параметра')

        if matches:
            return {
                'fields': matches,
                'score': len(matches)  # Простой рейтинг
            }

        return None

    # ================================================================
    # КОНВЕРТАЦИЯ В РЕЗУЛЬТАТ
    # ================================================================

    def _entity_to_result(self, entity: Entity, match_info: Dict) -> Dict:
        """Конвертирует сущность в результат поиска."""
        type_id = entity.type_id
        type_name = EntityType.get_name(type_id)
        icon = EntityType.get_icon(type_id)

        result = {
            'id': str(entity.id),
            'name': entity.c_name,
            'type': type_name,
            'type_id': type_id,
            'icon': icon,
            'match_fields': match_info.get('fields', []),
            'score': match_info.get('score', 0),
            'comment': entity.m_comment,
            'version': entity.n_relise,
            'is_active': entity.is_active,
            'dt_start': entity.dt_start.isoformat() if entity.dt_start else None,
            'dt_end': entity.dt_end.isoformat() if entity.dt_end else None
        }

        # Добавляем специфичные поля
        if type_id == EntityType.FILE:
            result['path'] = entity.j_data.get('full_path', '') if entity.j_data else ''
            result['is_python'] = entity.j_data.get('is_python', False) if entity.j_data else False
            result['size'] = entity.j_data.get('size_bytes', 0) if entity.j_data else 0

        elif type_id == EntityType.DIRECTORY:
            result['path'] = entity.j_data.get('full_path', '') if entity.j_data else ''

        elif type_id == EntityType.CLASS:
            result['bases'] = entity.j_data.get('bases', []) if entity.j_data else []
            result['is_dataclass'] = entity.j_data.get('is_dataclass', False) if entity.j_data else False
            # Находим родительский файл
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.METHOD:
            result['method_type'] = entity.j_data.get('method_type', 'instance') if entity.j_data else 'instance'
            result['is_async'] = entity.j_data.get('is_async', False) if entity.j_data else False
            result['return_type'] = entity.j_data.get('return_type', 'None') if entity.j_data else 'None'
            # Находим класс и файл
            result['class_id'] = entity.parent_id
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.PROCEDURE:
            result['is_async'] = entity.j_data.get('is_async', False) if entity.j_data else False
            result['return_type'] = entity.j_data.get('return_type', 'None') if entity.j_data else 'None'
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id in (EntityType.GLOBAL_VARIABLE, EntityType.LOCAL_VARIABLE, EntityType.CLASS_VARIABLE):
            result['var_type'] = entity.j_data.get('var_type', 'Any') if entity.j_data else 'Any'
            result['var_value'] = entity.j_data.get('var_value', '...') if entity.j_data else '...'
            result['is_constant'] = entity.j_data.get('is_constant', False) if entity.j_data else False
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.IMPORT:
            result['import_type'] = entity.j_data.get('import_type', 'import') if entity.j_data else 'import'
            result['module_path'] = entity.j_data.get('module_path', '') if entity.j_data else ''
            result['alias'] = entity.j_data.get('alias') if entity.j_data else None
            result['imported_names'] = entity.j_data.get('imported_names', []) if entity.j_data else []
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.HEADER:
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.PROPERTY:
            result['prop_type'] = entity.j_data.get('prop_type', 'Any') if entity.j_data else 'Any'
            result['is_readonly'] = entity.j_data.get('is_readonly', True) if entity.j_data else True
            result['class_id'] = entity.parent_id
            result['file_id'] = self._get_parent_file_id(entity)

        elif type_id == EntityType.PARAMETER:
            result['param_type'] = entity.j_data.get('param_type', 'Any') if entity.j_data else 'Any'
            result['default_value'] = entity.j_data.get('default_value') if entity.j_data else None
            result['is_required'] = entity.j_data.get('is_required', True) if entity.j_data else True
            result['parent_id'] = entity.parent_id
            result['file_id'] = self._get_parent_file_id(entity)

        return result

    def _get_parent_file_id(self, entity: Entity) -> Optional[str]:
        """Находит ID файла-родителя для сущности."""
        current = entity
        while current:
            if current.type_id == EntityType.FILE:
                return str(current.id)
            if current.parent_id:
                current = self.db_session.query(Entity).filter(
                    Entity.id == current.parent_id,
                    Entity.is_active == True
                ).first()
            else:
                break
        return None

    # ================================================================
    # РАСШИРЕННЫЙ ПОИСК
    # ================================================================

    def search_by_type(self, type_id: int, query: str = None) -> List[Dict]:
        """
        Ищет сущности определённого типа.
        """
        dt = self.view_time or datetime.now()

        entities = self.db_session.query(Entity).filter(
            Entity.type_id == type_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        )

        if query:
            q_lower = query.lower()
            entities = entities.filter(
                (Entity.c_name.ilike(f'%{query}%')) |
                (Entity.m_comment.ilike(f'%{query}%')) |
                (Entity.t_blobskript.ilike(f'%{query}%'))
            )

        result = []
        for entity in entities.all():
            match_info = self._check_match(entity, query.lower()) if query else {'fields': [], 'score': 1}
            result.append(self._entity_to_result(entity, match_info))

        return result

    def search_by_file(self, file_id: str, query: str = None) -> List[Dict]:
        """
        Ищет внутри конкретного файла.
        """
        dt = self.view_time or datetime.now()

        # Проверяем, что файл существует
        file_entity = self.db_session.query(Entity).filter(
            Entity.id == file_id,
            Entity.type_id == EntityType.FILE,
            Entity.is_active == True
        ).first()

        if not file_entity:
            return []

        # Ищем все дочерние сущности
        entities = self.db_session.query(Entity).filter(
            Entity.parent_id == file_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        )

        if query:
            q_lower = query.lower()
            entities = entities.filter(
                (Entity.c_name.ilike(f'%{query}%')) |
                (Entity.m_comment.ilike(f'%{query}%')) |
                (Entity.t_blobskript.ilike(f'%{query}%'))
            )

        result = []
        for entity in entities.all():
            match_info = self._check_match(entity, query.lower()) if query else {'fields': [], 'score': 1}
            result.append(self._entity_to_result(entity, match_info))

        return result

    def search_by_class(self, class_id: str, query: str = None) -> List[Dict]:
        """
        Ищет внутри конкретного класса.
        """
        dt = self.view_time or datetime.now()

        # Проверяем, что класс существует
        class_entity = self.db_session.query(Entity).filter(
            Entity.id == class_id,
            Entity.type_id == EntityType.CLASS,
            Entity.is_active == True
        ).first()

        if not class_entity:
            return []

        # Ищем все дочерние сущности (методы, свойства, переменные)
        entities = self.db_session.query(Entity).filter(
            Entity.parent_id == class_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        )

        if query:
            q_lower = query.lower()
            entities = entities.filter(
                (Entity.c_name.ilike(f'%{query}%')) |
                (Entity.m_comment.ilike(f'%{query}%')) |
                (Entity.t_blobskript.ilike(f'%{query}%'))
            )

        result = []
        for entity in entities.all():
            match_info = self._check_match(entity, query.lower()) if query else {'fields': [], 'score': 1}
            result.append(self._entity_to_result(entity, match_info))

        return result

    def search_code(self, query: str) -> List[Dict]:
        """
        Поиск по коду (t_blobskript).
        """
        dt = self.view_time or datetime.now()

        entities = self.db_session.query(Entity).filter(
            Entity.t_blobskript.ilike(f'%{query}%'),
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).all()

        result = []
        for entity in entities:
            # Находим строки с совпадением
            lines = []
            if entity.t_blobskript:
                for i, line in enumerate(entity.t_blobskript.split('\n')):
                    if query.lower() in line.lower():
                        lines.append({
                            'line_num': i + 1,
                            'text': line.strip()
                        })

            match_info = {'fields': ['код'], 'score': len(lines)}
            item = self._entity_to_result(entity, match_info)
            item['matches'] = lines
            result.append(item)

        return result


# ================================================================
# UI ДИАЛОГ ПОИСКА
# ================================================================

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
    QComboBox, QMessageBox, QApplication, QWidget,
    QSplitter, QTextEdit, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QTextCharFormat


class SearchDialog(QDialog):
    """Диалог глобального поиска."""

    # Сигнал для навигации
    navigate_to = Signal(str, str)  # entity_id, entity_type

    def __init__(self, parent=None, db_session=None, view_time: datetime = None):
        super().__init__(parent)
        self.db_session = db_session or get_session()
        self.view_time = view_time
        self.search_engine = CodeSearch(self.db_session, self.view_time)

        self.setWindowTitle("🔍 Глобальный поиск")
        self.resize(1000, 700)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Панель поиска
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска (минимум 2 символа)...")
        self.search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self.search_input, 3)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            'Все',
            'Файлы',
            'Каталоги',
            'Классы',
            'Методы',
            'Процедуры',
            'Переменные',
            'Импорты',
            'Заголовки',
            'Свойства'
        ])
        self.type_combo.setFixedWidth(120)
        search_layout.addWidget(self.type_combo, 1)

        self.btn_search = QPushButton("🔍 Найти")
        self.btn_search.clicked.connect(self._do_search)
        self.btn_search.setFixedWidth(100)
        search_layout.addWidget(self.btn_search)

        layout.addLayout(search_layout)

        # Основной сплиттер
        splitter = QSplitter(Qt.Vertical)

        # Верхняя часть — результаты
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Найдено", "Тип", "Где", "Версия"])
        self.results_tree.setColumnWidth(0, 350)
        self.results_tree.setColumnWidth(1, 120)
        self.results_tree.setColumnWidth(2, 300)
        self.results_tree.setColumnWidth(3, 80)
        self.results_tree.itemDoubleClicked.connect(self._on_result_clicked)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self._show_context_menu)

        results_layout.addWidget(self.results_tree)
        splitter.addWidget(results_widget)

        # Нижняя часть — предпросмотр
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_header = QHBoxLayout()
        preview_header.addWidget(QLabel("📄 Предпросмотр:"))
        preview_header.addStretch()

        self.preview_type_label = QLabel("")
        self.preview_type_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        preview_header.addWidget(self.preview_type_label)

        preview_layout.addLayout(preview_header)

        self.preview_edit = QTextEdit()
        self.preview_edit.setFont(QFont("Courier New", 10))
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setLineWrapMode(QTextEdit.NoWrap)
        preview_layout.addWidget(self.preview_edit)

        splitter.addWidget(preview_widget)
        splitter.setSizes([500, 200])

        layout.addWidget(splitter, 1)

        # Статусная строка
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Введите запрос и нажмите «Найти»")
        self.status_label.setStyleSheet("color: #6c757d; padding: 4px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #6c757d; padding: 4px;")
        status_layout.addWidget(self.count_label)

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setFixedWidth(100)
        status_layout.addWidget(self.btn_close)

        layout.addLayout(status_layout)

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query or len(query) < 2:
            QMessageBox.warning(self, "Предупреждение", "Введите минимум 2 символа")
            return

        search_type_map = {
            'Все': 'all',
            'Файлы': 'file',
            'Каталоги': 'directory',
            'Классы': 'class',
            'Методы': 'method',
            'Процедуры': 'procedure',
            'Переменные': 'variable',
            'Импорты': 'import',
            'Заголовки': 'header',
            'Свойства': 'property'
        }
        search_type = search_type_map.get(self.type_combo.currentText(), 'all')

        self.status_label.setText("⏳ Поиск...")
        self.results_tree.clear()
        self.preview_edit.clear()
        QApplication.processEvents()

        results = self.search_engine.search(query, search_type)

        if results.get('error'):
            self.status_label.setText(f"❌ {results['error']}")
            return

        total = results.get('total', 0)

        # Категории с иконками
        categories = [
            ('files', '📄 Файлы'),
            ('directories', '📁 Каталоги'),
            ('classes', '📦 Классы'),
            ('methods', '🔧 Методы'),
            ('procedures', '⚡ Процедуры'),
            ('variables', '🔤 Переменные'),
            ('imports', '📥 Импорты'),
            ('headers', '📝 Заголовки'),
            ('properties', '🔒 Свойства')
        ]

        for key, display_name in categories:
            items = results.get(key, [])
            if not items:
                continue

            cat_item = QTreeWidgetItem(self.results_tree)
            cat_item.setText(0, f"{display_name} ({len(items)})")
            cat_item.setExpanded(True)
            cat_item.setData(0, Qt.UserRole, {'type': 'category'})

            for item in sorted(items, key=lambda x: x.get('score', 0), reverse=True):
                child = QTreeWidgetItem(cat_item)

                # Имя с иконкой
                icon = item.get('icon', '•')
                name = item.get('name', '')
                child.setText(0, f"{icon} {name}")

                # Тип
                child.setText(1, item.get('type', ''))

                # Где находится (контекст)
                location = self._get_location(item)
                child.setText(2, location)

                # Версия
                child.setText(3, item.get('version', ''))

                # Сохраняем данные
                child.setData(0, Qt.UserRole, {
                    'id': item.get('id'),
                    'type': item.get('type'),
                    'type_id': item.get('type_id'),
                    'name': item.get('name')
                })

                # Подсветка совпадений в имени
                self._highlight_item(child, query)

        self.count_label.setText(f"Найдено: {total}")
        self.status_label.setText(f"✅ Поиск завершён. Найдено: {total}")

    def _get_location(self, item: Dict) -> str:
        """Определяет местоположение сущности."""
        type_id = item.get('type_id')

        if type_id == EntityType.FILE:
            return item.get('path', '')
        elif type_id == EntityType.DIRECTORY:
            return item.get('path', '')
        elif type_id == EntityType.CLASS:
            return f"в файле"
        elif type_id == EntityType.METHOD:
            return f"в классе"
        elif type_id == EntityType.PROCEDURE:
            return f"в файле"
        elif type_id in (EntityType.GLOBAL_VARIABLE, EntityType.LOCAL_VARIABLE, EntityType.CLASS_VARIABLE):
            return item.get('var_type', 'Any')
        elif type_id == EntityType.IMPORT:
            return item.get('module_path', '')
        elif type_id == EntityType.PROPERTY:
            return f"в классе"
        return ""

    def _highlight_item(self, item: QTreeWidgetItem, query: str):
        """Подсвечивает совпадения в имени."""
        text = item.text(0)
        if query.lower() in text.lower():
            # Находим позицию
            pos = text.lower().find(query.lower())
            # TODO: Подсветка через QTreeWidgetItem.setForeground
            # Пока просто устанавливаем жирный шрифт
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

    def _on_result_clicked(self, item, column):
        """Обработка двойного клика по результату."""
        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') == 'category':
            return

        entity_id = data.get('id')
        entity_type = data.get('type')

        # Показываем предпросмотр
        self._show_preview(entity_id)

        # Отправляем сигнал для навигации
        self.navigate_to.emit(entity_id, entity_type)

    def _show_preview(self, entity_id: str):
        """Показывает предпросмотр сущности."""
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            self.preview_edit.setPlainText("❌ Сущность не найдена")
            return

        self.preview_type_label.setText(f"{EntityType.get_icon(entity.type_id)} {EntityType.get_name(entity.type_id)}")

        preview_text = []

        # Имя
        preview_text.append(f"Имя: {entity.c_name}")
        preview_text.append(f"Тип: {EntityType.get_name(entity.type_id)}")
        preview_text.append("")

        # Комментарий
        if entity.m_comment:
            preview_text.append(f"Описание: {entity.m_comment}")
            preview_text.append("")

        # Код
        if entity.t_blobskript:
            preview_text.append("Код:")
            preview_text.append("```python")
            preview_text.append(entity.t_blobskript)
            preview_text.append("```")
        else:
            preview_text.append("(код отсутствует)")

        # Данные
        if entity.j_data:
            preview_text.append("")
            preview_text.append("Данные:")
            preview_text.append(str(entity.j_data))

        self.preview_edit.setPlainText("\n".join(preview_text))

    def _show_context_menu(self, position):
        """Показывает контекстное меню."""
        item = self.results_tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') == 'category':
            return

        menu = QMenu(self)

        action_show = QAction("👁️ Показать в дереве", self)
        action_show.triggered.connect(lambda: self._on_result_clicked(item, 0))
        menu.addAction(action_show)

        action_copy = QAction("📋 Копировать имя", self)
        action_copy.triggered.connect(lambda: self._copy_name(item))
        menu.addAction(action_copy)

        menu.exec_(self.results_tree.viewport().mapToGlobal(position))

    def _copy_name(self, item):
        """Копирует имя сущности в буфер обмена."""
        data = item.data(0, Qt.UserRole)
        if data:
            clipboard = QApplication.clipboard()
            clipboard.setText(data.get('name', ''))

    def navigate_to_entity(self, entity_id: str, entity_type: str = None):
        """Внешний метод для навигации."""
        self._show_preview(entity_id)


# ================================================================
# ФУНКЦИЯ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_search_dialog(parent=None, db_session=None, view_time: datetime = None):
    """Показывает диалог поиска."""
    dialog = SearchDialog(parent, db_session, view_time)
    return dialog.exec_()


# ================================================================
# ТЕСТ
# ================================================================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from analitik_core.database import init_db

    print("=" * 60)
    print("🧪 ТЕСТ ПОИСКА")
    print("=" * 60)

    if not init_db():
        print("❌ Не удалось подключиться к БД")
        sys.exit(1)

    app = QApplication(sys.argv)

    # Тестовый поиск
    search_engine = CodeSearch()
    results = search_engine.search("database", "all")

    print(f"\n📊 Результаты поиска 'database':")
    print(f"  Всего: {results.get('total', 0)}")
    print(f"  Файлы: {len(results.get('files', []))}")
    print(f"  Классы: {len(results.get('classes', []))}")
    print(f"  Методы: {len(results.get('methods', []))}")
    print(f"  Процедуры: {len(results.get('procedures', []))}")
    print(f"  Переменные: {len(results.get('variables', []))}")

    # Показываем диалог
    # show_search_dialog()

    sys.exit(0)