# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/collect_dialog.py
"""
Диалог сборки сущности (метода, класса, файла, каталога).
Версия: 2.3 — исправлены все относительные импорты
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QPushButton, QFrame,
    QMessageBox, QApplication, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QLineEdit,
    QFormLayout, QComboBox, QCheckBox, QGroupBox,
    QProgressDialog, QTreeWidgetItemIterator
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction
from sqlalchemy import text

# ================================================================
# АБСОЛЮТНЫЕ ИМПОРТЫ (вместо относительных)
# ================================================================
from analitik_core.models import Entity, EntityType
from analitik_core.database import get_db, get_session
from analitik_core.parser import PythonParser
from analitik_core.description_loader import DescriptionLoader
from analitik_compare import show_diff_dialog
from analitik_ui.ai_assistant_dialog import show_ai_assistant
# ================================================================


class CollectDialog(QDialog):
    """Диалог сборки сущности."""

    def __init__(self, entity_id: str, entity_name: str = None,
                 view_time: datetime = None, parent=None, db_session=None):
        super().__init__(parent)

        self.entity_id = entity_id
        self.entity_name = entity_name
        self.view_time = view_time or datetime.now()
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.description_loader = DescriptionLoader()

        # Получаем сущность
        self.entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not self.entity:
            QMessageBox.critical(self, "Ошибка", "Сущность не найдена")
            self.reject()
            return

        self._content = ""
        self._file_path = None
        self.entity_type_name = EntityType.get_name(self.entity.type_id)

        display_name = self.entity_name or self.entity.c_name
        self.setWindowTitle(f"📦 Сборка: {display_name} ({self.entity_type_name})")
        self.resize(900, 700)

        self._setup_ui()
        self._load_entity()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()

        info_text = f"📄 {self.entity.c_name} ({self.entity_type_name})"
        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.info_label)

        header.addStretch()

        time_text = f"⏱️ {self.view_time.strftime('%d.%m.%Y %H:%M')}"
        self.time_label = QLabel(time_text)
        self.time_label.setStyleSheet("color: #7f8c8d;")
        header.addWidget(self.time_label)

        layout.addLayout(header)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        info_layout = QHBoxLayout(info_frame)

        self.type_label = QLabel(f"Тип: {self.entity_type_name}")
        info_layout.addWidget(self.type_label)

        info_layout.addStretch()

        self.size_label = QLabel("Размер: 0 байт")
        info_layout.addWidget(self.size_label)

        layout.addWidget(info_frame)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.text_edit, 1)

        btn_layout = QHBoxLayout()

        self.btn_copy = QPushButton("📋 Копировать")
        self.btn_copy.clicked.connect(self._copy_content)
        btn_layout.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Сохранить в файл")
        self.btn_save.clicked.connect(self._save_to_file)
        btn_layout.addWidget(self.btn_save)

        self.btn_compare = QPushButton("📊 Сравнить с диском")
        self.btn_compare.clicked.connect(self._compare_with_disk)
        btn_layout.addWidget(self.btn_compare)

        self.btn_open_ai = QPushButton("🤖 ИИ-Помощник")
        self.btn_open_ai.clicked.connect(self._open_ai_assistant)
        btn_layout.addWidget(self.btn_open_ai)

        btn_layout.addStretch()

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _load_entity(self):
        """Загружает сущность из БД."""
        try:
            if self.entity.type_id == EntityType.FILE:
                self._load_file()
            elif self.entity.type_id == EntityType.CLASS:
                self._load_class()
            elif self.entity.type_id == EntityType.METHOD:
                self._load_method()
            elif self.entity.type_id == EntityType.PROCEDURE:
                self._load_procedure()
            elif self.entity.type_id == EntityType.DIRECTORY:
                self._load_directory()
            else:
                self._load_generic()

            self.text_edit.setPlainText(self._content)
            self.size_label.setText(f"Размер: {len(self._content.encode('utf-8'))} байт")

        except Exception as e:
            self.text_edit.setPlainText(f"❌ Ошибка загрузки: {str(e)}")

    def _load_file(self):
        """Загружает файл."""
        lines = []
        lines.append(f"# Файл: {self.entity.c_name}")
        lines.append(f"# Путь: {self.entity.j_data.get('full_path', 'неизвестно') if self.entity.j_data else 'неизвестно'}")
        lines.append(f"# Размер: {self.entity.j_data.get('size_bytes', 0) if self.entity.j_data else 0} байт")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        lines.append("")

        # Собираем содержимое файла из дочерних сущностей
        children = self.db_session.query(Entity).filter(
            Entity.parent_id == self.entity.id,
            Entity.is_active == True
        ).order_by(Entity.type_id, Entity.n_order).all()

        # Заголовок
        headers = [c for c in children if c.type_id == EntityType.HEADER]
        if headers:
            lines.append(f'"""\n{headers[0].t_blobskript}\n"""')
            lines.append("")

        # Импорты
        imports = [c for c in children if c.type_id == EntityType.IMPORT]
        for imp in imports:
            lines.append(imp.t_blobskript or imp.c_name)
        if imports:
            lines.append("")

        # Глобальные переменные
        globals_ = [c for c in children if c.type_id == EntityType.GLOBAL_VARIABLE]
        for var in globals_:
            v_type = var.j_data.get('var_type', 'Any') if var.j_data else 'Any'
            v_value = var.j_data.get('var_value', '...') if var.j_data else '...'
            lines.append(f"{var.c_name}: {v_type} = {v_value}")
        if globals_:
            lines.append("")

        # Процедуры
        procedures = [c for c in children if c.type_id == EntityType.PROCEDURE]
        for proc in procedures:
            if proc.t_blobskript:
                lines.append(proc.t_blobskript)
                lines.append("")

        # Классы
        classes = [c for c in children if c.type_id == EntityType.CLASS]
        for cls in classes:
            self._append_class(cls, lines)

        self._content = "\n".join(lines)

    def _load_class(self):
        """Загружает класс."""
        lines = []
        lines.append(f"# Класс: {self.entity.c_name}")
        bases = self.entity.j_data.get('bases', []) if self.entity.j_data else []
        lines.append(f"# Базовые классы: {', '.join(bases) if bases else 'object'}")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        if self.entity.t_blobskript:
            lines.append("")
            lines.append(self.entity.t_blobskript)

        # Методы класса
        methods = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.METHOD,
            Entity.parent_id == self.entity.id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for method in methods:
            if method.t_blobskript:
                lines.append("")
                lines.append(f"    # {method.m_comment}" if method.m_comment else "")
                code_lines = method.t_blobskript.split('\n')
                for code_line in code_lines:
                    lines.append(f"    {code_line}")

        # Свойства
        props = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROPERTY,
            Entity.parent_id == self.entity.id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for prop in props:
            if prop.t_blobskript:
                lines.append("")
                code_lines = prop.t_blobskript.split('\n')
                for code_line in code_lines:
                    lines.append(f"    {code_line}")

        self._content = "\n".join(lines)

    def _load_method(self):
        """Загружает метод."""
        lines = []
        lines.append(f"# Метод: {self.entity.c_name}()")
        m_type = self.entity.j_data.get('method_type', 'instance') if self.entity.j_data else 'instance'
        lines.append(f"# Тип: {m_type}")
        lines.append(f"# Возвращает: {self.entity.j_data.get('return_type', 'Any') if self.entity.j_data else 'Any'}")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        # Параметры
        params = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PARAMETER,
            Entity.parent_id == self.entity.id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        if params:
            lines.append("")
            lines.append("# Параметры:")
            for param in params:
                p_type = param.j_data.get('param_type', 'Any') if param.j_data else 'Any'
                default = param.j_data.get('default_value') if param.j_data else None
                required = param.j_data.get('is_required', True) if param.j_data else True
                lines.append(f"#   - {param.c_name}: {p_type}" + (f" = {default}" if not required else ""))

        if self.entity.t_blobskript:
            lines.append("")
            lines.append(self.entity.t_blobskript)

        self._content = "\n".join(lines)

    def _load_procedure(self):
        """Загружает процедуру."""
        lines = []
        lines.append(f"# Процедура: {self.entity.c_name}()")
        lines.append(f"# Асинхронная: {self.entity.j_data.get('is_async', False) if self.entity.j_data else False}")
        lines.append(f"# Возвращает: {self.entity.j_data.get('return_type', 'Any') if self.entity.j_data else 'Any'}")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        if self.entity.t_blobskript:
            lines.append("")
            lines.append(self.entity.t_blobskript)

        self._content = "\n".join(lines)

    def _load_directory(self):
        """Загружает каталог."""
        lines = []
        lines.append(f"# Каталог: {self.entity.c_name}")
        lines.append(f"# Путь: {self.entity.j_data.get('full_path', 'неизвестно') if self.entity.j_data else 'неизвестно'}")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        # Содержимое каталога
        children = self.db_session.query(Entity).filter(
            Entity.parent_id == self.entity.id,
            Entity.is_active == True
        ).order_by(Entity.type_id, Entity.c_name).all()

        if children:
            lines.append("")
            lines.append("# Содержимое:")

            for child in children:
                icon = EntityType.get_icon(child.type_id)
                type_name = EntityType.get_name(child.type_id)
                lines.append(f"#   {icon} {child.c_name} ({type_name})")

        self._content = "\n".join(lines)

    def _load_generic(self):
        """Загружает любую сущность."""
        lines = []
        lines.append(f"# Сущность: {self.entity.c_name}")
        lines.append(f"# Тип: {self.entity_type_name}")

        if self.entity.m_comment:
            lines.append(f"# Описание: {self.entity.m_comment}")

        if self.entity.t_blobskript:
            lines.append("")
            lines.append(self.entity.t_blobskript)

        if self.entity.j_data:
            lines.append("")
            lines.append("# Данные:")
            lines.append(str(self.entity.j_data))

        self._content = "\n".join(lines)

    def _append_class(self, cls_entity: Entity, lines: List[str]):
        """Добавляет класс в список строк."""
        if cls_entity.t_blobskript:
            lines.append(cls_entity.t_blobskript)

        # Методы
        methods = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.METHOD,
            Entity.parent_id == cls_entity.id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for method in methods:
            if method.t_blobskript:
                lines.append("")
                code_lines = method.t_blobskript.split('\n')
                for code_line in code_lines:
                    lines.append(f"    {code_line}")

        lines.append("")

    def _copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)
        QMessageBox.information(self, "Успех", "📋 Содержимое скопировано в буфер обмена")

    def _save_to_file(self):
        if not self._content:
            QMessageBox.warning(self, "Ошибка", "Нет содержимого для сохранения")
            return

        base_name = self.entity.c_name
        default_name = f"{base_name}_{self.view_time.strftime('%Y%m%d_%H%M')}.py"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            default_name,
            "Python files (*.py);;All files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self._content)
            QMessageBox.information(self, "Успех", f"💾 Файл сохранён:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _compare_with_disk(self):
        """Сравнивает собранный код с файлом на диске."""
        # Ищем файл на диске
        full_path = self.entity.j_data.get('full_path') if self.entity.j_data else None
        if not full_path or not os.path.exists(full_path):
            QMessageBox.warning(self, "Ошибка", "Файл на диске не найден")
            return

        # Используем абсолютный импорт
        from analitik_compare import show_diff_dialog
        show_diff_dialog(
            entity_id=self.entity_id,
            entity_name=self.entity.c_name,
            parent=self,
            db_session=self.db_session,
            view_time=self.view_time
        )

    def _open_ai_assistant(self):
        """Открывает ИИ-помощника."""
        from analitik_ui.ai_assistant_dialog import show_ai_assistant
        show_ai_assistant(
            entity_id=self.entity_id,
            entity_name=self.entity.c_name,
            parent=self,
            db_session=self.db_session,
            view_time=self.view_time
        )


# ================================================================
# ДИАЛОГ ВЫБОРА КАТАЛОГА ДЛЯ СБОРКИ
# ================================================================

class CollectDirectoryDialog(QDialog):
    """Диалог выбора каталога для сборки."""

    def __init__(self, directory_id: str, directory_name: str,
                 view_time: datetime = None, parent=None, db_session=None):
        super().__init__(parent)

        self.directory_id = directory_id
        self.directory_name = directory_name
        self.view_time = view_time or datetime.now()
        self.db_session = db_session or get_session()
        self.db = get_db()

        self.selected_target = None
        self.create_new = False
        self.new_name = ""

        self.setWindowTitle(f"📁 Сборка каталога: {directory_name}")
        self.resize(600, 500)

        self._setup_ui()
        self._load_directories()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            f"📁 Сборка каталога: {self.directory_name}\n"
            f"Выберите целевой каталог или создайте новый."
            f"\n⏱️ {self.view_time.strftime('%d.%m.%Y %H:%M')}"
        )
        info.setStyleSheet("font-weight: bold; padding: 8px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(info)

        group_existing = QGroupBox("📂 Выбрать существующий каталог")
        group_layout = QVBoxLayout(group_existing)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Каталог", "Путь"])
        self.tree.setColumnWidth(0, 200)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        group_layout.addWidget(self.tree)

        layout.addWidget(group_existing)

        group_new = QGroupBox("📁 Создать новый каталог")
        new_layout = QHBoxLayout(group_new)

        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Введите имя нового каталога...")
        new_layout.addWidget(self.new_name_edit, 1)

        self.btn_create = QPushButton("➕ Создать")
        self.btn_create.clicked.connect(self._create_new)
        new_layout.addWidget(self.btn_create)

        layout.addWidget(group_new)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_ok = QPushButton("✅ Собрать сюда")
        self.btn_ok.clicked.connect(self._accept_selection)
        self.btn_ok.setEnabled(False)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("✖ Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _load_directories(self):
        self.tree.clear()

        dt = self.view_time or datetime.now()

        with self.db.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT d.id, d.c_name, d.j_data
                    FROM mozart.tbl_entity d
                    WHERE d.type_id = 1
                      AND d.parent_id IS NULL
                      AND d.dt_start <= :dt
                      AND (d.dt_end IS NULL OR d.dt_end > :dt)
                    ORDER BY d.c_name
                """),
                {'dt': dt}
            )
            dirs = result.fetchall()

        for d in dirs:
            full_path = d.j_data.get('full_path') if d.j_data else ''
            item = QTreeWidgetItem(self.tree)
            item.setText(0, f"📁 {d.c_name}")
            item.setText(1, full_path)
            item.setData(0, Qt.UserRole, str(d.id))
            self._load_subdirectories(item, str(d.id), dt)

        self.tree.expandAll()

    def _load_subdirectories(self, parent_item, parent_id, dt: datetime):
        with self.db.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT d.id, d.c_name, d.j_data
                    FROM mozart.tbl_entity d
                    WHERE d.type_id = 1
                      AND d.parent_id = :parent_id
                      AND d.dt_start <= :dt
                      AND (d.dt_end IS NULL OR d.dt_end > :dt)
                    ORDER BY d.c_name
                """),
                {'parent_id': parent_id, 'dt': dt}
            )
            dirs = result.fetchall()

        for d in dirs:
            full_path = d.j_data.get('full_path') if d.j_data else ''
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"📁 {d.c_name}")
            item.setText(1, full_path)
            item.setData(0, Qt.UserRole, str(d.id))
            self._load_subdirectories(item, str(d.id), dt)

    def _on_item_double_clicked(self, item, column):
        self._select_directory(item)

    def _select_directory(self, item):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            iterator.value().setSelected(False)
            iterator += 1

        item.setSelected(True)
        self.selected_target = item.data(0, Qt.UserRole)
        self.create_new = False
        self.btn_ok.setEnabled(True)

    def _create_new(self):
        name = self.new_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя каталога")
            return

        self.selected_target = None
        self.create_new = True
        self.new_name = name
        self.btn_ok.setEnabled(True)

    def _accept_selection(self):
        self.accept()

    def get_result(self):
        return {
            'target_id': self.selected_target,
            'create_new': self.create_new,
            'new_name': self.new_name
        }


# ================================================================
# ФУНКЦИИ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_collect_dialog(entity_id: str, entity_name: str = None,
                        view_time: datetime = None, parent=None, db_session=None):
    """Показывает диалог сборки сущности."""
    dialog = CollectDialog(entity_id, entity_name, view_time, parent, db_session)
    return dialog.exec_()


def show_collect_directory_dialog(directory_id: str, directory_name: str,
                                  view_time: datetime = None, parent=None, db_session=None):
    """Показывает диалог выбора каталога для сборки."""
    dialog = CollectDirectoryDialog(directory_id, directory_name, view_time, parent, db_session)
    if dialog.exec_():
        return dialog.get_result()
    return None