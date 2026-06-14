# tabs/import_tab.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from mozart_import.dialogs.profile_manager_dialog import ProfileManagerDialog
from mozart_import.core.profile_manager import ProfileManager
from mozart_import.core.models import SourceType


class ImportTab(QWidget):
    """Главная вкладка управления импортом данных."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.profile_manager = ProfileManager(self.db)
        self.init_ui()
        self.retranslate_ui()
        self.load_profiles()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Кнопки управления профилями (первая строка)
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_profile)
        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_profile)
        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_profile)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Таблица профилей импорта
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('profile_name'),
            self.translator.tr('source_type'),
            self.translator.tr('source_path'),
            self.translator.tr('import_mode')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_profile)
        layout.addWidget(self.table)

        # Кнопки действий с профилем (вторая строка)
        action_layout = QHBoxLayout()
        self.btn_refresh = QPushButton(self.translator.tr('btn_refresh'))
        self.btn_refresh.clicked.connect(self.load_profiles)
        self.btn_import = QPushButton(self.translator.tr('btn_start_import'))
        self.btn_import.clicked.connect(self.run_import)
        action_layout.addWidget(self.btn_refresh)
        action_layout.addWidget(self.btn_import)
        action_layout.addStretch()
        layout.addLayout(action_layout)

    def retranslate_ui(self):
        self.btn_add.setText(self.translator.tr('btn_add'))
        self.btn_edit.setText(self.translator.tr('btn_edit'))
        self.btn_delete.setText(self.translator.tr('btn_delete'))
        self.btn_refresh.setText(self.translator.tr('btn_refresh'))
        self.btn_import.setText(self.translator.tr('btn_start_import'))
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('profile_name'),
            self.translator.tr('source_type'),
            self.translator.tr('source_path'),
            self.translator.tr('import_mode')
        ])

    def load_profiles(self):
        """Загружает список профилей в таблицу."""
        profiles = self.profile_manager.list_profiles()
        self.table.setRowCount(0)
        for profile in profiles:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(profile.id)))
            self.table.setItem(row, 1, QTableWidgetItem(profile.name))
            self.table.setItem(row, 2, QTableWidgetItem(profile.source_type.value if profile.source_type else ""))
            self.table.setItem(row, 3, QTableWidgetItem(profile.source_path))
            import_mode = getattr(profile, 'import_mode', 'append')
            mode_text = self.translator.tr('import_mode_append') if import_mode == 'append' else self.translator.tr(
                'import_mode_full_update')
            self.table.setItem(row, 4, QTableWidgetItem(mode_text))
            self.table.item(row, 0).setData(Qt.UserRole, profile.id)

    def get_selected_profile_id(self):
        current = self.table.currentRow()
        if current >= 0:
            return self.table.item(current, 0).data(Qt.UserRole)
        return None

    def add_profile(self):
        """Создаёт новый профиль импорта."""
        self.open_profile_manager()

    def open_profile_manager(self):
        """Открывает диалог управления профилями импорта."""
        dlg = ProfileManagerDialog(self.db, self)
        dlg.exec_()
        self.load_profiles()  # обновляем таблицу после закрытия диалога

    def edit_profile(self):
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_profile_first'))
            return
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            QMessageBox.critical(self, self.translator.tr('error'), self.translator.tr('profile_load_error'))
            return

        # Открываем конструктор импорта с выбранным профилем
        from mozart_import.connectors.file_connector import FileConnector
        from mozart_import.connectors.db_connector import DBConnector
        from mozart_import.connectors.url_connector import URLConnector
        from mozart_import.designer.designer_v2 import ImportDesignerV2
        from mozart_import.core.models import SourceType, FileFormat

        try:
            if profile.source_type == SourceType.FILE:
                connector = FileConnector(profile.source_path, FileFormat(profile.file_format))
            elif profile.source_type == SourceType.DATABASE:
                connector = DBConnector("", db_type=profile.db_type, host=profile.db_host,
                                        port=profile.db_port, database=profile.db_name,
                                        user=profile.db_user, password=profile.db_pass)
            else:
                connector = URLConnector(profile.source_path)
            connector.connect()

            designer = ImportDesignerV2(self.db, connector, self)
            designer.editing_profile_id = profile.id
            designer.load_profile_links(profile)
            designer.show()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def delete_profile(self):
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_profile_first'))
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('delete_profile_confirm')) == QMessageBox.Yes:
            self.profile_manager.delete_profile(profile_id)
            self.load_profiles()

    def run_import(self):
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_profile_first'))
            return
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            QMessageBox.critical(self, self.translator.tr('error'), self.translator.tr('profile_load_error'))
            return

        # Открываем конструктор импорта и сразу запускаем импорт
        from mozart_import.connectors.file_connector import FileConnector
        from mozart_import.connectors.db_connector import DBConnector
        from mozart_import.connectors.url_connector import URLConnector
        from mozart_import.designer.designer_v2 import ImportDesignerV2
        from mozart_import.core.models import SourceType, FileFormat

        try:
            if profile.source_type == SourceType.FILE:
                connector = FileConnector(profile.source_path, FileFormat(profile.file_format))
            elif profile.source_type == SourceType.DATABASE:
                connector = DBConnector("", db_type=profile.db_type, host=profile.db_host,
                                        port=profile.db_port, database=profile.db_name,
                                        user=profile.db_user, password=profile.db_pass)
            else:
                connector = URLConnector(profile.source_path)
            connector.connect()

            designer = ImportDesignerV2(self.db, connector, self)
            designer.editing_profile_id = profile.id
            designer.load_profile_links(profile)
            designer.show()
            # Автоматически запускаем импорт
            designer.perform_import()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))