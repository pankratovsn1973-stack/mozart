# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_main.py
"""
Аналитик Моцарт — главная точка входа.
Версия: 4.2 — кнопка очистки БД, улучшенный парсер, тёмная тема
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel, QFrame,
    QMessageBox, QProgressDialog, QMenuBar, QMenu, QStatusBar,
    QDateTimeEdit, QTabWidget, QTreeWidgetItemIterator,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog,
    QSplitter, QGroupBox, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QDateTime, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QFont

from sqlalchemy import text
from analitik_core.assembler import CodeAssembler
from analitik_ui.assemble_dialog import AssemblePreviewDialog

# Добавляем путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ================================================================
# ИМПОРТЫ МОДУЛЕЙ
# ================================================================

from analitik_core.database import (
    init_db, get_session, get_db, get_config,
    get_schema_name, get_project_root,
    get_ignore_dirs, get_ignore_extensions, get_include_only_python
)
from analitik_core.models import Entity, EntityType
from analitik_scanner.loader import load_project
from analitik_compare import show_diff_dialog
from analitik_search import show_search_dialog
from analitik_ui.tree_tasks import TreeTasks
from analitik_export import show_export_import_dialog
from analitik_sync import SyncManager
from analitik_ui.ai_assistant_dialog import show_ai_assistant
from analitik_ui.collect_dialog import show_collect_dialog, show_collect_directory_dialog
from analitik_ui.usage_dialog import show_usage_dialog

try:
    from analitik_gateway import GatewayManager
except ImportError:
    GatewayManager = None


# ================================================================
# ДИАЛОГИ НАСТРОЙКИ
# ================================================================

class SchemaDialog(QDialog):
    """Диалог создания схемы."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Создание схемы")
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Для работы Аналитика Моцарт требуется схема в базе данных.\n"
            "Введите имя схемы (латиница, без пробелов):"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.schema_edit = QLineEdit()
        self.schema_edit.setPlaceholderText("mozart")
        self.schema_edit.setText("mozart")
        form.addRow("Имя схемы:", self.schema_edit)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_schema_name(self) -> str:
        return self.schema_edit.text().strip()


class ProjectRootDialog(QDialog):
    """Диалог выбора корня проекта."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📁 Выбор корня проекта")
        self.resize(500, 150)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Укажите корневую директорию проекта, которую нужно анализировать.\n"
            "Все пути будут сохраняться относительно этой директории."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("/home/user/my_project")
        form.addRow("Корень проекта:", self.path_edit)

        btn_browse = QPushButton("📂 Обзор...")
        btn_browse.clicked.connect(self._browse)
        form.addRow("", btn_browse)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _browse(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите корневую директорию проекта",
            os.path.expanduser("~")
        )
        if dir_path:
            self.path_edit.setText(dir_path)

    def get_root_path(self) -> str:
        return self.path_edit.text().strip()


# ================================================================
# ВИДЖЕТ ПУТЕШЕСТВИЯ ВО ВРЕМЕНИ
# ================================================================

class TimeTravelWidget(QWidget):
    """Виджет управления временем (путешествие во времени)."""
    time_changed = Signal(datetime)
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_view_time = None

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel("⏱️ Просмотр на дату:")
        layout.addWidget(label)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("dd.MM.yyyy HH:mm:ss")
        self.datetime_edit.setCalendarPopup(True)
        layout.addWidget(self.datetime_edit)

        self.btn_apply = QPushButton("Показать")
        self.btn_apply.clicked.connect(self._apply_time)
        layout.addWidget(self.btn_apply)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedWidth(2)
        layout.addWidget(sep)

        self.btn_reset = QPushButton("↺ Текущий")
        self.btn_reset.clicked.connect(self._reset_time)
        layout.addWidget(self.btn_reset)

        self.status_label = QLabel("🟢 Текущий")
        self.status_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.setStyleSheet("""
            QDateTimeEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton {
                background-color: #094771;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0a5c8a;
            }
            QPushButton#btn_reset {
                background-color: #e67e22;
            }
            QPushButton#btn_reset:hover {
                background-color: #d35400;
            }
        """)
        self.btn_reset.setObjectName("btn_reset")

    def _apply_time(self):
        dt = self.datetime_edit.dateTime().toPython()
        self._current_view_time = dt
        self.status_label.setText(f"📅 {dt.strftime('%d.%m.%Y %H:%M')}")
        self.status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")
        self.time_changed.emit(dt)

    def _reset_time(self):
        now = QDateTime.currentDateTime()
        self.datetime_edit.setDateTime(now)
        self._current_view_time = None
        self.status_label.setText("🟢 Текущий")
        self.status_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        self.reset_requested.emit()

    def get_view_time(self) -> Optional[datetime]:
        return self._current_view_time

    def is_traveling(self) -> bool:
        return self._current_view_time is not None


# ================================================================
# ГЛАВНОЕ ОКНО
# ================================================================

class AnalitikMozartMain(QMainWindow):
    """Главное окно Аналитика Моцарт."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Аналитик Моцарт — Конструктор кода")
        self.resize(1400, 900)

        # Параметры
        self.project_root = None
        self.db_config_file = None
        self.db_session = None
        self._view_time = None
        self.db = None
        self._config = None

        self.sync_manager = None
        self.sync_enabled = False

        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

        self._initialize()

    # ================================================================
    # ИНИЦИАЛИЗАЦИЯ
    # ================================================================

    def _initialize(self):
        """Инициализирует БД и загружает конфигурацию."""
        config_file = self._find_config_file()

        if config_file:
            if init_db(config_file):
                self.db_session = get_session()
                self.db = get_db()
                self._config = get_config()
                self.db_config_file = config_file

                if hasattr(self, 'tree_tasks'):
                    self.tree_tasks.update_session(self.db_session, self.db)

                self.project_root = get_project_root()

                if self.project_root and os.path.exists(self.project_root):
                    self.statusBar.showMessage(
                        f"✅ Подключено (схема: {get_schema_name()}, корень: {self.project_root})"
                    )
                    self.refresh_tree()
                    return
                else:
                    self._setup_project_root()
                    return
            else:
                self._handle_db_connection_error()
                return
        else:
            self._handle_no_config_file()
            return

    def _find_config_file(self) -> Optional[str]:
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

    def _handle_no_config_file(self):
        reply = QMessageBox.question(
            self,
            "Файл конфигурации не найден",
            "Файл db.mzt не найден.\n"
            "Хотите создать новый или выбрать существующий?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self._create_or_select_config()
        else:
            self.statusBar.showMessage("❌ Работа невозможна без файла конфигурации")

    def _create_or_select_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл db.mzt",
            os.path.expanduser("~"),
            "MZT files (*.mzt);;All files (*)"
        )
        if file_path:
            if init_db(file_path):
                self.db_session = get_session()
                self.db = get_db()
                self._config = get_config()
                self.db_config_file = file_path
                self.project_root = get_project_root()
                if self.project_root and os.path.exists(self.project_root):
                    self.statusBar.showMessage(f"✅ Подключено (корень: {self.project_root})")
                    self.refresh_tree()
                    return
                else:
                    self._setup_project_root()
                    return
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
                return

        reply = QMessageBox.question(
            self,
            "Создать новый конфиг?",
            "Файл не выбран. Создать новый db.mzt в текущей директории?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            default_path = os.path.join(os.getcwd(), "db.mzt")
            config = {
                "db": {
                    "host": "localhost",
                    "port": "5432",
                    "name": "mozart_erp",
                    "user": "postgres",
                    "pass": "",
                    "schema": "mozart"
                },
                "project": {
                    "root": "",
                    "ignore_dirs": [
                        "__pycache__", ".git", ".svn", ".hg", ".idea", ".vscode",
                        ".venv", "venv", "env", ".env", "node_modules", "build",
                        "dist", ".pytest_cache", ".mypy_cache", ".tox",
                        ".ipynb_checkpoints", ".DS_Store", "Thumbs.db",
                        "logs", "backup", "old", "tmp", "backups"
                    ],
                    "ignore_extensions": [
                        ".pyc", ".pyo", ".so", ".dll", ".dylib",
                        ".exe", ".bin", ".dat", ".db", ".sqlite", ".sqlite3"
                    ],
                    "include_only_python": True
                }
            }
            try:
                with open(default_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Успех", f"Создан {default_path}")

                if init_db(default_path):
                    self.db_session = get_session()
                    self.db = get_db()
                    self._config = get_config()
                    self.db_config_file = default_path
                    self._setup_project_root()
                    return
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл: {e}")

    def _handle_db_connection_error(self):
        dialog = SchemaDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            schema_name = dialog.get_schema_name()
            if not schema_name:
                QMessageBox.warning(self, "Ошибка", "Имя схемы не может быть пустым")
                return

            if self._config:
                self._config.save_schema(schema_name)

            if init_db(self.db_config_file):
                self.db_session = get_session()
                self.db = get_db()
                self._config = get_config()
                self.project_root = get_project_root()
                if self.project_root and os.path.exists(self.project_root):
                    self.statusBar.showMessage(f"✅ Схема {schema_name} создана")
                    self.refresh_tree()
                    return
                else:
                    self._setup_project_root()
                    return
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать схему {schema_name}")

    def _setup_project_root(self):
        dialog = ProjectRootDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            root_path = dialog.get_root_path()
            if not root_path or not os.path.exists(root_path):
                QMessageBox.warning(self, "Ошибка", "Укажите существующую директорию")
                self._setup_project_root()
                return

            if self._config:
                self._config.save_project_root(root_path)
            self.project_root = root_path
            self.statusBar.showMessage(f"✅ Корень проекта установлен: {root_path}")
            self.refresh_tree()
        else:
            self.statusBar.showMessage("❌ Корень проекта не задан")

    # ================================================================
    # НАСТРОЙКА UI
    # ================================================================

    def _setup_menu(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("📁 Файл")
        action_load = file_menu.addAction("🔄 Загрузить проект")
        action_load.triggered.connect(self.load_project)
        action_sync_force = file_menu.addAction("⚡ Принудительная синхронизация")
        action_sync_force.triggered.connect(self._force_sync)
        file_menu.addSeparator()
        action_exit = file_menu.addAction("🚪 Выход")
        action_exit.triggered.connect(self.close)

        # Вид
        view_menu = menubar.addMenu("👁️ Вид")
        action_refresh = view_menu.addAction("🔄 Обновить дерево")
        action_refresh.triggered.connect(self.refresh_tree)
        view_menu.addSeparator()
        action_today = view_menu.addAction("📅 Текущий момент")
        action_today.triggered.connect(self._reset_to_today)

        # Поиск
        search_menu = menubar.addMenu("🔍 Поиск")
        action_search = search_menu.addAction("🔍 Глобальный поиск")
        action_search.setShortcut(QKeySequence("Ctrl+F"))
        action_search.triggered.connect(self._show_search)
        search_menu.addAction(action_search)

        # Экспорт
        export_menu = menubar.addMenu("📦 Экспорт")
        action_export = export_menu.addAction("📤 Экспорт/Импорт данных")
        action_export.triggered.connect(self._show_export_import)
        export_menu.addAction(action_export)

        # Синхронизация
        sync_menu = menubar.addMenu("🔄 Синхр.")
        action_sync_start = sync_menu.addAction("▶️ Запустить автосинхронизацию")
        action_sync_start.triggered.connect(self._start_sync)
        action_sync_stop = sync_menu.addAction("⏹️ Остановить автосинхронизацию")
        action_sync_stop.triggered.connect(self._stop_sync)
        sync_menu.addSeparator()
        action_sync_force = sync_menu.addAction("⚡ Принудительная синхронизация")
        action_sync_force.triggered.connect(self._force_sync)
        sync_menu.addSeparator()
        action_sync_status = sync_menu.addAction("📊 Статус")
        action_sync_status.triggered.connect(self._show_sync_status)

        # PyCharm
        pycharm_menu = menubar.addMenu("🔗 PyCharm")
        action_open_pycharm = pycharm_menu.addAction("📂 Открыть в PyCharm")
        action_open_pycharm.triggered.connect(self._open_in_pycharm)
        if GatewayManager:
            action_open_gateway = pycharm_menu.addAction("📂 Открыть в PyCharm (Шлюз)")
            action_open_gateway.triggered.connect(self._open_in_pycharm_gateway)

        # Помощь
        help_menu = menubar.addMenu("❓ Помощь")
        action_about = help_menu.addAction("ℹ️ О программе")
        action_about.triggered.connect(self.show_about)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Панель управления
        control_layout = QHBoxLayout()

        self.btn_load = QPushButton("🔄 Загрузить проект")
        self.btn_load.clicked.connect(self.load_project)
        control_layout.addWidget(self.btn_load)

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.refresh_tree)
        control_layout.addWidget(self.btn_refresh)

        self.btn_sync_force = QPushButton("⚡ Синхр.")
        self.btn_sync_force.clicked.connect(self._force_sync)
        control_layout.addWidget(self.btn_sync_force)

        self.btn_assemble = QPushButton("🔧 Собрать файл")
        self.btn_assemble.clicked.connect(self._show_assemble_dialog)
        self.btn_assemble.setToolTip("Собрать файл из частей и показать результат")
        control_layout.addWidget(self.btn_assemble)

        self.btn_search = QPushButton("🔍 Поиск")
        self.btn_search.clicked.connect(self._show_search)
        control_layout.addWidget(self.btn_search)

        self.btn_export = QPushButton("📦 Экспорт")
        self.btn_export.clicked.connect(self._show_export_import)
        control_layout.addWidget(self.btn_export)

        self.btn_sync = QPushButton("🔄 Авто")
        self.btn_sync.clicked.connect(self._toggle_sync)
        self.btn_sync.setFixedWidth(80)
        control_layout.addWidget(self.btn_sync)

        self.btn_pycharm = QPushButton("🔗 PyCharm")
        self.btn_pycharm.clicked.connect(self._open_in_pycharm)
        self.btn_pycharm.setFixedWidth(90)
        control_layout.addWidget(self.btn_pycharm)

        # Кнопка очистки БД
        self.btn_clear_db = QPushButton("🗑️ Очистить БД")
        self.btn_clear_db.clicked.connect(self._clear_database)
        self.btn_clear_db.setStyleSheet("background-color: #c0392b; color: white;")
        control_layout.addWidget(self.btn_clear_db)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Путешествие во времени
        self.time_travel = TimeTravelWidget()
        self.time_travel.time_changed.connect(self._on_time_changed)
        self.time_travel.reset_requested.connect(self._reset_to_today)
        layout.addWidget(self.time_travel)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Вкладки
        self.tabs = QTabWidget()

        # Вкладка "Код"
        self.tree_code_widget = QWidget()
        tree_code_layout = QVBoxLayout(self.tree_code_widget)
        tree_code_layout.setContentsMargins(0, 0, 0, 0)

        info_layout = QHBoxLayout()
        self.info_label = QLabel("📂 Структура проекта")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #d4d4d4;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(self.count_label)
        tree_code_layout.addLayout(info_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Элемент", "Тип", "Статус", "Версия"])
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 120)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)

        tree_code_layout.addWidget(self.tree, 1)
        self.tabs.addTab(self.tree_code_widget, "📂 Код")

        # Вкладка "Задачи"
        self.tree_tasks = TreeTasks(self, None, self._view_time)
        self.tabs.addTab(self.tree_tasks, "📋 Задачи")

        layout.addWidget(self.tabs, 1)

        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("color: #888888; padding: 4px;")
        layout.addWidget(self.status_label)

    def _setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
# показать сборку
    def _show_assemble_dialog(self):
        """Показывает диалог сборки файла из частей."""
        # Проверяем, что выбран элемент в дереве
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите файл в дереве")
            return

        data = current_item.data(0, Qt.UserRole)
        if not data or data.get('type') != 'entity':
            QMessageBox.warning(self, "Ошибка", "Выберите сущность")
            return

        entity_id = data.get('id')
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            QMessageBox.warning(self, "Ошибка", "Сущность не найдена")
            return

        # Если это не файл — ищем родительский файл
        file_id = self._get_file_id(entity)
        if not file_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти файл")
            return

        # Собираем файл
        from analitik_core.assembler import assemble_file, assemble_class

        assembler = CodeAssembler(self.db_session)
        assembled_text = assembler.assemble_file(file_id)

        if not assembled_text:
            QMessageBox.warning(self, "Ошибка", "Не удалось собрать файл")
            return

        # Показываем диалог
        dialog = AssemblePreviewDialog(
            file_id=file_id,
            assembled_text=assembled_text,
            parent=self,
            db_session=self.db_session
        )
        dialog.exec_()

    def _get_file_id(self, entity: Entity) -> Optional[str]:
        """Находит ID файла для любой сущности."""
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
    # ДЕРЕВО КОДА
    # ================================================================

    def refresh_tree(self):
        """Обновляет дерево кода."""
        self.tree.clear()

        if not self.db_session or not self.db:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "⏳ Подключение к базе данных...")
            return

        if not self.project_root:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "⚠️ Корень проекта не задан")
            return

        dt = self._view_time or datetime.now()

        # Ищем корневой каталог
        root_entity = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.DIRECTORY,
            Entity.parent_id.is_(None),
            Entity.is_active == True
        ).first()

        if not root_entity:
            # Ищем любой каталог без родителя
            root_entity = self.db_session.query(Entity).filter(
                Entity.type_id == EntityType.DIRECTORY,
                Entity.parent_id.is_(None),
                Entity.is_active == True
            ).first()

        if root_entity:
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, f"📁 {root_entity.c_name}")
            root_item.setText(1, "каталог")
            root_item.setText(2, "активен" if root_entity.is_active else "закрыт")
            root_item.setText(3, root_entity.dt_start.strftime('%d.%m.%Y') if root_entity.dt_start else '')
            root_item.setData(0, Qt.UserRole, {'type': 'entity', 'id': str(root_entity.id)})
            root_item.setExpanded(True)

            self._load_entity_tree(root_item, str(root_entity.id), dt)

        total_items = 0
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            total_items += 1
            iterator += 1

        self.count_label.setText(f"Элементов: {total_items}")

        if hasattr(self, 'tree_tasks'):
            self.tree_tasks.view_time = self._view_time
            self.tree_tasks.refresh()

        if self._view_time:
            self.statusBar.showMessage(f"📅 Просмотр на {self._view_time.strftime('%d.%m.%Y %H:%M:%S')}")
        else:
            self.statusBar.showMessage("📅 Текущий момент")

    def _load_entity_tree(self, parent_item, parent_id, dt: datetime):
        """Загружает дерево сущностей."""
        # Загружаем дочерние сущности
        children = self.db_session.query(Entity).filter(
            Entity.parent_id == parent_id,
            Entity.is_active == True,
            Entity.dt_start <= dt,
            (Entity.dt_end.is_(None) | (Entity.dt_end > dt))
        ).order_by(Entity.type_id, Entity.n_order, Entity.c_name).all()

        for entity in children:
            type_name = EntityType.get_name(entity.type_id)
            icon = EntityType.get_icon(entity.type_id)

            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"{icon} {entity.c_name}")
            item.setText(1, type_name)
            item.setText(2, "активен" if entity.is_active else "закрыт")
            item.setText(3, entity.dt_start.strftime('%d.%m.%Y') if entity.dt_start else '')

            if entity.m_comment:
                item.setToolTip(0, entity.m_comment)

            item.setData(0, Qt.UserRole, {'type': 'entity', 'id': str(entity.id)})

            # Если это каталог или класс — загружаем дальше
            if entity.type_id in (EntityType.DIRECTORY, EntityType.CLASS, EntityType.FILE):
                # Для файлов загружаем содержимое, если это Python файл
                if entity.type_id == EntityType.FILE:
                    is_python = entity.j_data.get('is_python', False) if entity.j_data else False
                    if is_python:
                        self._load_entity_tree(item, str(entity.id), dt)
                else:
                    self._load_entity_tree(item, str(entity.id), dt)

            parent_item.setExpanded(True)

    # ================================================================
    # ОБРАБОТКА СОБЫТИЙ
    # ================================================================

    def _on_time_changed(self, view_time: datetime):
        self._view_time = view_time
        self.statusBar.showMessage(f"📅 Просмотр на {view_time.strftime('%d.%m.%Y %H:%M:%S')}")
        self.refresh_tree()

    def _reset_to_today(self):
        self._view_time = None
        self.statusBar.showMessage("📅 Текущий момент")
        self.refresh_tree()

    def _on_tree_double_click(self, item, column):
        """Обработка двойного клика по элементу дерева."""
        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') != 'entity':
            return

        entity_id = data.get('id')
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if entity:
            self._show_collect(entity)

    # ================================================================
    # КОНТЕКСТНОЕ МЕНЮ
    # ================================================================

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') != 'entity':
            return

        entity_id = data.get('id')
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return

        menu = QMenu(self)

        # Основные действия
        action_collect = QAction("📦 Собрать", self)
        action_collect.triggered.connect(lambda: self._show_collect(entity))
        menu.addAction(action_collect)

        action_compare = QAction("📊 Сравнить с диском", self)
        action_compare.triggered.connect(lambda: self._show_diff(entity))
        menu.addAction(action_compare)

        menu.addSeparator()

        # Действия для кода
        if entity.type_id in (EntityType.CLASS, EntityType.METHOD, EntityType.PROCEDURE):
            action_ai = QAction("🤖 ИИ-Помощник", self)
            action_ai.triggered.connect(lambda: self._show_ai_assistant(entity))
            menu.addAction(action_ai)

            action_usage = QAction("🕸️ Найти использования", self)
            action_usage.triggered.connect(lambda: self._show_usage(entity))
            menu.addAction(action_usage)

        # Действия для файлов
        if entity.type_id == EntityType.FILE:
            menu.addSeparator()

            full_path = entity.j_data.get('full_path') if entity.j_data else None
            if full_path:
                action_open = QAction("📂 Открыть в редакторе", self)
                action_open.triggered.connect(lambda: self._open_file(full_path))
                menu.addAction(action_open)

                action_copy = QAction("📋 Копировать путь", self)
                action_copy.triggered.connect(lambda: self._copy_path(full_path))
                menu.addAction(action_copy)

                action_pycharm = QAction("🔗 Открыть в PyCharm", self)
                action_pycharm.triggered.connect(lambda: self._open_file_in_pycharm(full_path))
                menu.addAction(action_pycharm)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    # ================================================================
    # ДЕЙСТВИЯ
    # ================================================================

    def _show_collect(self, entity: Entity):
        show_collect_dialog(
            entity_id=str(entity.id),
            entity_name=entity.c_name,
            view_time=self._view_time,
            parent=self,
            db_session=self.db_session
        )

    def _show_diff(self, entity: Entity):
        show_diff_dialog(
            entity_id=str(entity.id),
            entity_name=entity.c_name,
            parent=self,
            db_session=self.db_session,
            view_time=self._view_time
        )

    def _show_ai_assistant(self, entity: Entity):
        show_ai_assistant(
            entity_id=str(entity.id),
            entity_name=entity.c_name,
            parent=self,
            db_session=self.db_session,
            view_time=self._view_time
        )

    def _show_usage(self, entity: Entity):
        show_usage_dialog(
            entity_id=str(entity.id),
            entity_name=entity.c_name,
            parent=self,
            db_session=self.db_session,
            view_time=self._view_time
        )

    def _show_search(self):
        show_search_dialog(self, self.db_session, self._view_time)

    def _show_export_import(self):
        show_export_import_dialog(self, self.db_session)

    def _open_file(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return

        try:
            # Используем системный редактор по умолчанию
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path], check=False)
            elif sys.platform == 'win32':  # Windows
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=False)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def _open_file_in_pycharm(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return

        try:
            if file_path.endswith('.py'):
                subprocess.Popen(['pycharm-community', '--line', '1', file_path])
            else:
                self._open_file(file_path)
        except FileNotFoundError:
            try:
                subprocess.Popen(['pycharm', '--line', '1', file_path])
            except FileNotFoundError:
                QMessageBox.warning(self, "Ошибка", "PyCharm не найден\nУстановите pycharm-community или pycharm")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть PyCharm: {e}")

    def _copy_path(self, file_path: str):
        if not file_path:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)
        self.statusBar.showMessage("📋 Путь скопирован в буфер обмена")

    def _open_in_pycharm(self):
        if not self.project_root:
            QMessageBox.warning(self, "Ошибка", "Корень проекта не задан")
            return

        try:
            subprocess.Popen(['pycharm-community', self.project_root])
        except FileNotFoundError:
            try:
                subprocess.Popen(['pycharm', self.project_root])
            except FileNotFoundError:
                QMessageBox.warning(self, "Ошибка", "PyCharm не найден")

    def _open_in_pycharm_gateway(self):
        if not self.project_root:
            QMessageBox.warning(self, "Ошибка", "Корень проекта не задан")
            return

        if not GatewayManager:
            QMessageBox.warning(self, "Ошибка", "Модуль шлюза не найден")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Система выгрузит актуальные версии файлов из БД во временную папку\n"
            "и откроет её в PyCharm.\n\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog("Подготовка рабочего пространства...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()

        try:
            gateway = GatewayManager(self.project_root, db_session=self.db_session)
            success = gateway.prepare_workspace(self._view_time)

            progress.close()

            if success:
                work_path = gateway.get_work_path()
                try:
                    subprocess.Popen(['pycharm-community', work_path])
                except FileNotFoundError:
                    try:
                        subprocess.Popen(['pycharm', work_path])
                    except FileNotFoundError:
                        QMessageBox.warning(self, "Ошибка", "PyCharm не найден")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось подготовить файлы")

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))

    # ================================================================
    # ОЧИСТКА БАЗЫ ДАННЫХ
    # ================================================================

    def _clear_database(self):
        """Очищает базу данных через хранимую функцию."""
        reply = QMessageBox.question(
            self,
            "⚠️ Очистка базы данных",
            "Вы действительно хотите удалить ВСЕ данные из базы?\n\n"
            "⚠️ Это действие НЕОБРАТИМО!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog("Очистка базы данных...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()

        try:
            with self.db.engine.connect() as conn:
                result = conn.execute(text("SELECT mozart.clear_database();"))
                row = result.fetchone()
                message = row[0] if row else "База данных очищена"
                conn.commit()

            progress.close()

            # Обновляем дерево
            self.refresh_tree()

            QMessageBox.information(
                self,
                "Успех",
                f"✅ {message}"
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", f"Не удалось очистить БД: {e}")

    # ================================================================
    # ЗАГРУЗКА ПРОЕКТА
    # ================================================================

    def load_project(self):
        if not self.db_session:
            QMessageBox.warning(self, "Ошибка", "Нет подключения к БД")
            return

        if not self.project_root:
            QMessageBox.warning(self, "Ошибка", "Корень проекта не задан")
            self._setup_project_root()
            return

        if self.time_travel.is_traveling():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы находитесь в режиме просмотра прошлого.\n"
                "Загрузка проекта обновит данные и сбросит просмотр.\nПродолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            self._reset_to_today()

        progress = QProgressDialog("Загрузка проекта...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            stats = load_project(self.project_root)
            progress.close()

            QMessageBox.information(
                self,
                "Загрузка завершена",
                f"📊 Статистика:\n"
                f"  - Каталогов: {stats.get('directories', 0)}\n"
                f"  - Файлов: {stats.get('files', 0)}\n"
                f"  - Классов: {stats.get('classes', 0)}\n"
                f"  - Методов: {stats.get('methods', 0)}\n"
                f"  - Процедур: {stats.get('procedures', 0)}\n"
                f"  - Переменных: {stats.get('variables', 0)}\n"
                f"  - Импортов: {stats.get('imports', 0)}\n"
                f"  - Вызовов: {stats.get('calls', 0)}\n"
                f"  - Обогащено описаниями: {stats.get('enriched', 0)}"
            )

            self.refresh_tree()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _force_sync(self):
        if not self.db_session:
            QMessageBox.warning(self, "Ошибка", "Нет подключения к БД")
            return

        if not self.project_root:
            QMessageBox.warning(self, "Ошибка", "Корень проекта не задан")
            return

        reply = QMessageBox.question(
            self,
            "Принудительная синхронизация",
            "Это обновит все данные в БД по текущему состоянию проекта.\n\n"
            "⚠️ Все изменения в БД, не сохранённые в файлах, будут потеряны!\n\n"
            "Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog("Принудительная синхронизация...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            stats = load_project(self.project_root)
            progress.close()

            QMessageBox.information(
                self,
                "Синхронизация завершена",
                f"📊 Результаты:\n"
                f"  - Каталогов: {stats.get('directories', 0)}\n"
                f"  - Файлов: {stats.get('files', 0)}\n"
                f"  - Классов: {stats.get('classes', 0)}\n"
                f"  - Методов: {stats.get('methods', 0)}\n"
                f"  - Процедур: {stats.get('procedures', 0)}\n"
                f"  - Переменных: {stats.get('variables', 0)}\n"
                f"  - Импортов: {stats.get('imports', 0)}\n"
                f"  - Вызовов: {stats.get('calls', 0)}"
            )

            self.refresh_tree()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))

    # ================================================================
    # СИНХРОНИЗАЦИЯ
    # ================================================================

    def _toggle_sync(self):
        if self.sync_enabled:
            self._stop_sync()
        else:
            self._start_sync()

    def _start_sync(self):
        if not self.db_session:
            QMessageBox.warning(self, "Ошибка", "Нет подключения к БД")
            return

        if not self.project_root:
            QMessageBox.warning(self, "Ошибка", "Корень проекта не задан")
            return

        if self.sync_manager and self.sync_manager.is_running():
            QMessageBox.information(self, "Информация", "Синхронизация уже запущена")
            return

        self.sync_manager = SyncManager(self.project_root, self.db_session)

        def on_sync_event(event_type, path, data):
            if event_type == 'modified':
                self.statusBar.showMessage(f"📝 Изменён: {os.path.basename(path)}")
            elif event_type == 'created':
                self.statusBar.showMessage(f"📄 Создан: {os.path.basename(path)}")
            elif event_type == 'deleted':
                self.statusBar.showMessage(f"🗑️ Удалён: {os.path.basename(path)}")
            elif event_type == 'started':
                self.statusBar.showMessage(f"🔄 Автосинхронизация запущена")
            elif event_type == 'stopped':
                self.statusBar.showMessage(f"⏹️ Автосинхронизация остановлена")
            elif event_type == 'error':
                self.statusBar.showMessage(f"❌ Ошибка: {data}")

            QTimer.singleShot(500, self.refresh_tree)

        if self.sync_manager.start(on_sync_event):
            self.sync_enabled = True
            self.btn_sync.setText("⏹️ Авто")
            self.btn_sync.setStyleSheet("background-color: #c0392b; color: white;")
            self.statusBar.showMessage("🔄 Автосинхронизация запущена")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось запустить синхронизацию")

    def _stop_sync(self):
        if self.sync_manager:
            self.sync_manager.stop()
            self.sync_enabled = False
            self.btn_sync.setText("🔄 Авто")
            self.btn_sync.setStyleSheet("")
            self.statusBar.showMessage("⏹️ Автосинхронизация остановлена")

    def _show_sync_status(self):
        if self.sync_manager:
            status = self.sync_manager.get_status()
            QMessageBox.information(
                self,
                "Статус синхронизации",
                f"🔄 Автосинхронизация: {'✅ Запущена' if status['running'] else '⏹️ Остановлена'}\n"
                f"📁 Проект: {status['project_root']}\n"
                f"👁️ Наблюдатель: {'✅ Активен' if status['observer_active'] else '❌ Неактивен'}"
            )
        else:
            QMessageBox.information(self, "Статус", "🔄 Автосинхронизация не запущена")

    # ================================================================
    # О ПРОГРАММЕ
    # ================================================================

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "🎵 Аналитик Моцарт\n"
            "Версия 4.2 — Everything is a Node\n\n"
            "Инструмент для анализа структуры кода.\n"
            "Хранит код в базе данных с полной историей.\n\n"
            "🆕 Возможности:\n"
            "  • Единая таблица сущностей (tbl_entity)\n"
            "  • Дерево кода с версионностью\n"
            "  • Дерево задач (задачи → архитектура → планы → действия)\n"
            "  • Путешествие во времени\n"
            "  • Обогащение из документации\n"
            "  • Сравнение с диском\n"
            "  • Глобальный поиск\n"
            "  • Экспорт/Импорт данных\n"
            "  • Автосинхронизация с файловой системой\n"
            "  • ИИ-Помощник (генерация промптов)\n"
            "  • Интеграция с PyCharm\n"
            "  • Граф вызовов\n"
            "  • Сборка сущностей\n"
            "  • Очистка базы данных\n\n"
            "⏱️ Путешествие во времени:\n"
            "  • Выберите дату в календаре\n"
            "  • Нажмите «Показать»\n"
            "  • Нажмите «↺ Текущий» для возврата"
        )


# ================================================================
# ЗАПУСК
# ================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }

        /* ============================================================
           ДЕРЕВО
           ============================================================ */
        QTreeWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            color: #000000;
            gridline-color: #e0e0e0;
            font-size: 12px;
        }
        QTreeWidget::item {
            padding: 4px 8px;
            color: #000000;
        }
        QTreeWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QTreeWidget::item:hover {
            background-color: #e8f0fe;
        }
        QTreeWidget::item:!selected {
            color: #000000;
        }
        QTreeWidget::item:has-children {
            color: #000000;
            font-weight: bold;
        }

        QHeaderView::section {
            background-color: #e8e8e8;
            color: #000000;
            padding: 4px;
            border: none;
            font-weight: bold;
        }

        /* ============================================================
           ВКЛАДКИ
           ============================================================ */
        QTabWidget::pane {
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #e8e8e8;
            color: #000000;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QTabBar::tab:hover:!selected {
            background-color: #d0d0d0;
        }

        /* ============================================================
           КНОПКИ
           ============================================================ */
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        QPushButton:pressed {
            background-color: #005a9e;
        }
        QPushButton:disabled {
            background-color: #d0d0d0;
            color: #888888;
        }

        QPushButton#btn_clear_db {
            background-color: #d32f2f;
            color: #ffffff;
        }
        QPushButton#btn_clear_db:hover {
            background-color: #b71c1c;
        }

        QPushButton#btn_sync {
            background-color: #e8e8e8;
            color: #000000;
        }
        QPushButton#btn_sync:checked {
            background-color: #d32f2f;
            color: #ffffff;
        }

        /* ============================================================
           ОКНО СРАВНЕНИЯ (DiffDialog)
           ============================================================ */
        QDialog#DiffDialog {
            background-color: #f5f5f5;
        }

        QDialog#DiffDialog QLabel {
            color: #000000;
        }

        QDialog#DiffDialog QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            font-family: "Courier New", monospace;
            font-size: 11px;
        }

        QDialog#DiffDialog QFrame {
            background-color: #f5f5f5;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }

        QDialog#DiffDialog QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QDialog#DiffDialog QPushButton:hover {
            background-color: #106ebe;
        }
        QDialog#DiffDialog QPushButton:disabled {
            background-color: #d0d0d0;
            color: #888888;
        }

        /* Панели сравнения */
        QDialog#DiffDialog QFrame#db_panel {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }
        QDialog#DiffDialog QFrame#disk_panel {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }

        /* Заголовки панелей сравнения */
        QDialog#DiffDialog QLabel#panel_title {
            background-color: #e8e8e8;
            color: #000000;
            padding: 6px 12px;
            font-weight: bold;
            border-bottom: 1px solid #d0d0d0;
        }

        /* Статусные строки в панелях сравнения */
        QDialog#DiffDialog QLabel#panel_status {
            background-color: #f8f9fa;
            color: #6c757d;
            padding: 2px 8px;
            border-top: 1px solid #d0d0d0;
            font-size: 10px;
        }

        /* ============================================================
           ОБЩИЕ ЭЛЕМЕНТЫ
           ============================================================ */
        QStatusBar {
            background-color: #f0f0f0;
            color: #000000;
        }

        QMenuBar {
            background-color: #f0f0f0;
            color: #000000;
        }
        QMenuBar::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
        }
        QMenu::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QDateTimeEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 4px 8px;
        }

        QLabel {
            color: #000000;
        }

        QFrame {
            color: #000000;
        }

        QProgressDialog {
            background-color: #ffffff;
            color: #000000;
        }

        QLineEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QLineEdit:focus {
            border: 1px solid #0078d4;
        }

        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
        }

        QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }

        QCheckBox {
            color: #000000;
        }

        QGroupBox {
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: #000000;
        }

        QDialog {
            background-color: #f0f0f0;
        }
        QDialog QLabel {
            color: #000000;
        }
        QDialog QLineEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QDialog QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QDialog QPushButton:hover {
            background-color: #106ebe;
        }

        QTableWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            gridline-color: #e0e0e0;
        }
        QTableWidget::item {
            color: #000000;
        }
        QTableWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #a0a0a0;
        }

        QSplitter::handle {
            background-color: #d0d0d0;
        }
        QSplitter::handle:hover {
            background-color: #b0b0b0;
        }
    """)
    window = AnalitikMozartMain()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

