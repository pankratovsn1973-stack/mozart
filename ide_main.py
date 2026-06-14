# ide_main.py
# -*- coding: utf-8 -*-
"""
Главный стартовый модуль интегрированной среды разработки (IDE) Mozart ERP.
Инициализирует окно конфигуратора, управляет файлами проектов .mzt и сессиями БД.
Исправлен критический баг блокировки кликов мыши в Linux в диалогах QFileDialog.
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QSplitter, QStatusBar, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Твои оригинальные импорты ядра системы
from ide_core import goProject
from ide_db_work import DBWorkDialog
from lang.local_translator import LocalTranslator
from database import DatabaseService

# Импортируем вынесенную UI-логику панелей для соблюдения лимита < 300 строк
from ide_ui_panels import MozartIDEPanelsMixin

class MozartIDE(QMainWindow, MozartIDEPanelsMixin):
    """
    Главное окно IDE Mozart ERP.
    Управляет жизненным циклом конфигурационных файлов и подключением к PostgreSQL.
    """
    def __init__(self):
        super().__init__()
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('window_title_main'))
        self.resize(1100, 700)

        # Словарь для хранения действий меню
        self.actions = {}

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Сплиттер
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Левая панель (настройки подключения)
        left = self._create_left_panel()
        splitter.addWidget(left)

        # Правая панель (кнопки управления)
        right = self._create_right_panel()
        splitter.addWidget(right)

        splitter.setSizes([450, 650])

        # Статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(self.translator.tr('status_ready'))

        # Меню
        self._init_menu()

        # Переменные состояния
        self.current_project_file = None
        self.buttons_enabled = False
        self.db_work_dialog = None  # ссылка на диалог, если открыт

        self.retranslate_ui()

    def _init_menu(self):
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu(self.translator.tr('menu_file'))
        self.actions['file_menu'] = file_menu

        new_act = QAction(self.translator.tr('action_new_project'), self)
        new_act.triggered.connect(self.new_project)
        file_menu.addAction(new_act)
        self.actions['new_project'] = new_act

        open_act = QAction(self.translator.tr('action_open_project'), self)
        open_act.triggered.connect(self.open_project)
        file_menu.addAction(open_act)
        self.actions['open_project'] = open_act

        save_act = QAction(self.translator.tr('action_save_project'), self)
        save_act.triggered.connect(self.save_project)
        file_menu.addAction(save_act)
        self.actions['save_project'] = save_act

        file_menu.addSeparator()

        exit_act = QAction(self.translator.tr('action_exit'), self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        self.actions['exit'] = exit_act

        # Меню "Язык"
        lang_menu = menubar.addMenu(self.translator.tr('menu_language'))
        self.actions['lang_menu'] = lang_menu
        languages = [
            ('ru', 'Русский'),
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('zh', '中文'),
            ('tt', 'Татарча')
        ]
        for code, name in languages:
            action = QAction(name, self)
            action.setData(code)
            action.triggered.connect(lambda checked, lang=code: self.change_language(lang))
            lang_menu.addAction(action)

        # Меню "Помощь"
        help_menu = menubar.addMenu(self.translator.tr('menu_help'))
        self.actions['help_menu'] = help_menu
        about_act = QAction(self.translator.tr('action_about'), self)
        about_act.triggered.connect(self.about)
        help_menu.addAction(about_act)
        self.actions['about'] = about_act

    def change_language(self, lang_code):
        self.translator.set_language(lang_code)
        self.retranslate_ui()
        if self.db_work_dialog and self.db_work_dialog.isVisible():
            self.db_work_dialog.retranslate_ui()

    # --- Методы работы с проектом ---
    def new_project(self):
        goProject.__init__()
        self.current_project_file = None
        self._clear_connection_fields()
        self.btn_connect.setEnabled(True)
        self.statusBar.showMessage(self.translator.tr('status_new_project'))

    def open_project(self):
        """ИСПРАВЛЕНО: Добавлен DontUseNativeDialog для разблокировки мыши в Linux."""
        path, _ = QFileDialog.getOpenFileName(
            self, self.translator.tr('dialog_open_project'), "",
            "Mozart Project (*.mzt);;All files (*)",
            options=QFileDialog.DontUseNativeDialog  # ЖЕЛЕЗНЫЙ ФИКС КЛИКОВ МЫШИ
        )
        if not path:
            return
        ok, msg = goProject.p_LoadProject(path)
        if ok:
            self.current_project_file = path
            self._update_connection_fields()
            self.btn_connect.setEnabled(True)
            self.statusBar.showMessage(self.translator.tr('status_project_loaded') + f" {os.path.basename(path)}")
        else:
            QMessageBox.critical(self, self.translator.tr('error_loading'), msg)

    def save_project(self):
        """ИСПРАВЛЕНО: Добавлен DontUseNativeDialog при сохранении файла."""
        if not self.current_project_file:
            path, _ = QFileDialog.getSaveFileName(
                self, self.translator.tr('dialog_save_project'), "",
                "Mozart Project (*.mzt)",
                options=QFileDialog.DontUseNativeDialog  # Фикс мыши при сохранении
            )
            if path:
                if not path.lower().endswith(".mzt"):
                    path += ".mzt"
                self.current_project_file = path
        if self.current_project_file:
            goProject.p_SaveProject(self.current_project_file)
            self.statusBar.showMessage(self.translator.tr('status_project_saved') + f" {os.path.basename(self.current_project_file)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Гарантируем наличие рабочей папки для локальных форм
    FORMS_DIR = os.path.join(os.path.dirname(__file__), "forms")
    os.makedirs(FORMS_DIR, exist_ok=True)

    # Принудительно устанавливаем светлую тему Fusion
    app.setStyle("Fusion")

    # Глобальные QSS стили приложения Mozart
    app.setStyleSheet("""
        QWidget, QDialog, QMainWindow {
            background-color: #f0f0f0;
            color: #000000;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #a0a0a0;
            padding: 5px;
            border-radius: 3px;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
            background-color: white;
            border: 1px solid #a0a0a0;
            border-radius: 3px;
        }
        QTreeWidget, QTableWidget {
            background-color: white;
            alternate-background-color: #f5f5f5;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #a0a0a0;
        }
    """)

    window = MozartIDE()
    window.show()
    sys.exit(app.exec())
