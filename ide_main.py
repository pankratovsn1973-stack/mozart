# ide_main.py
# -*- coding: utf-8 -*-
"""
Главный стартовый модуль интегрированной среды разработки (IDE) Mozart ERP.
Инициализирует окно конфигуратора, управляет файлами проектов .mzt и сессиями БД.
Исправлен критический баг блокировки кликов мыши в Linux в диалогах QFileDialog.
"""

import sys
import os
# 🚀 КРИТИЧЕСКИЙ ФИКС ДЛЯ LINUX: Принудительно отключаем сырой Wayland-плагин Qt,
# переключая графический стек на железобетонно стабильный X11 (Xwayland / xcb).
# Это полностью предотвратит падение процесса с ошибкой Fatal Error / Exit code 255.
os.environ["QT_QPA_PLATFORM"] = "xcb"


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

        # Системное динамическое обновление кэша через ключ перевода
        sync_act = QAction(self.translator.tr('action_refresh_lang'), self)
        sync_act.triggered.connect(self.force_reload_translations)
        lang_menu.addAction(sync_act)
        self.actions['sync_translations'] = sync_act
        lang_menu.addSeparator()

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

        # Временная диагностика
        diag_act = QAction("Диагностика методов", self)
        diag_act.triggered.connect(self._run_methods_diagnostics)
        help_menu.addAction(diag_act)



        self.actions['about'] = about_act

    def change_language(self, lang_code):
        self.translator.set_language(lang_code)
        self.retranslate_ui()
        if self.db_work_dialog and self.db_work_dialog.isVisible():
            self.db_work_dialog.retranslate_ui()

    def force_reload_translations(self):
        """Ручной вызов обновления кэша переводов из Postgres без перезапуска приложения.
        Полностью локализован, сообщения вычитываются через ключи переводов.
        """
        # Проверяем подключение через голый системный флаг ядра
        if not getattr(goProject, 'db_conn', None):
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('err_no_db_connection')
            )
            return

        try:
            db_service = DatabaseService()
            # Вызываем твой метод перезагрузки кэша внутри LocalTranslator
            self.translator.reload_from_postgres(db_service)

            # Принудительно обновляем все строки главного окна конфигуратора
            self.retranslate_ui()

            # Если диалог работы с сущностями открыт, заставляем его тоже перерисовать свои вкладки
            if self.db_work_dialog and self.db_work_dialog.isVisible():
                self.db_work_dialog.retranslate_ui()

            self.statusBar.showMessage(self.translator.tr('msg_translations_refreshed'))

        except Exception as e:
            # Форматируем системное исключение внутрь локализованной строки
            error_template = self.translator.tr('err_translations_refresh_failed')
            error_msg = error_template.format(str(e))

            QMessageBox.critical(
                self,
                self.translator.tr('error'),
                error_msg
            )

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

# Конец файла: ide_main.py
# Размещаем слот синхронизации времени сессии внутри контроллера MozartIDE

    def about(self):
        """Окно информации о конфигураторе."""
        QMessageBox.about(self, self.translator.tr('action_about'),
                          "MOZART ERP Configurator\nВерсия 0.1\nРазработано на PySide6")

        # Фрагмент файла: ide_main.py
        # Синхронизация прогрева кэша мостов при изменении системного времени сессии

    def on_system_date_changed(self, datetime_val):
        """Слот, обновляющий глобальное время сессии и очищающий ОЗУ от устаревших версий."""
        goProject.system_date = datetime_val

        # Системный вызов: сжигаем в памяти неактуальные версии классов
        if hasattr(goProject, 'class_registry') and goProject.class_registry:
            goProject.class_registry.sync_registry_with_session_date()

        # Актуализируем кэш декларативных мостов из СУБД под текущий контекст
        if hasattr(goProject, 'property_bridge_manager') and goProject.property_bridge_manager:
            goProject.property_bridge_manager.init_and_warm_cache()

        formatted_time = datetime_val.toString("dd.MM.yyyy HH:mm:ss")
        # 🚀 ФИКС v8.1: Убираем круглые скобки у self.statusBar, так как это объект, а не функция
        self.statusBar.showMessage(f"Системное время сессии изменено на: {formatted_time}. Кэш ОЗУ очищен.")


    def _run_methods_diagnostics(self):
        """Временная диагностика: проверка sub_method_bridges в ОЗУ."""
        if not getattr(goProject, 'db_conn', None):
            QMessageBox.warning(self, "Диагностика", "Сначала подключитесь к БД")
            return

        node = goProject.class_registry.get_class_version(1)  # MozartTextBox
        if node is None:
            QMessageBox.warning(self, "Диагностика", "Класс 1 не загружен")
            return

        lines = [
            f"Класс: {node.class_name} (ID: {node.version_id})",
            f"c_base_class: {node.c_base_class}",
            f"sub_methods: {list(node.sub_methods.keys())}",
            f"sub_method_bridges: {list(node.sub_method_bridges.keys())}",
            f"has_method('mydefault'): {node.has_method('mydefault')}",
            f"resolve_method('mydefault'): {repr(node.resolve_method('mydefault'))}",
        ]
        QMessageBox.information(self, "Диагностика методов", "\n".join(lines))



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
