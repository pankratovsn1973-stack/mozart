# mozart_import/dialogs/profile_manager_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,                              QTableWidgetItem, QPushButton, QMessageBox, QHeaderView,                              QComboBox, QGroupBox, QLabel, QLineEdit, QFileDialog,                              QDialogButtonBox)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from ..core.profile_manager import ProfileManager
from ..designer.designer_v2 import ImportDesignerV2
from ..designer.scene_profile_adapter import SceneProfileAdapter
from ..connectors.file_connector import FileConnector
from ..connectors.db_connector import DBConnector
from ..connectors.url_connector import URLConnector
from ..core.models import SourceType, FileFormat


class ProfileManagerDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.prof_manager = ProfileManager(self.db)
        self.setWindowTitle(self.translator.tr('profile_manager_title'))
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('profile_id'),
            self.translator.tr('profile_name'),
            self.translator.tr('source_type'),
            self.translator.tr('created_at')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.translator.tr('profile_add'))
        self.btn_add.clicked.connect(self.add_profile)
        self.btn_edit = QPushButton(self.translator.tr('profile_edit'))
        self.btn_edit.clicked.connect(self.edit_profile)
        self.btn_delete = QPushButton(self.translator.tr('profile_delete'))
        self.btn_delete.clicked.connect(self.delete_profile)
        self.btn_close = QPushButton(self.translator.tr('close'))
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.load_profiles()

    def load_profiles(self):
        profiles = self.prof_manager.list_profiles()
        self.table.setRowCount(len(profiles))
        for row, prof in enumerate(profiles):
            self.table.setItem(row, 0, QTableWidgetItem(str(prof.id)))
            self.table.setItem(row, 1, QTableWidgetItem(prof.name))
            self.table.setItem(row, 2, QTableWidgetItem(prof.source_type.value if prof.source_type else ''))
            self.table.setItem(row, 3, QTableWidgetItem(str(prof.created_at) if hasattr(prof, 'created_at') else ''))
            self.table.item(row, 0).setData(Qt.UserRole, prof.id)

    def get_selected_profile_id(self):
        current = self.table.currentRow()
        if current >= 0:
            return self.table.item(current, 0).data(Qt.UserRole)
        return None

    def add_profile(self):
        self.run_import_designer()

    def edit_profile(self):
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('select_profile_first'))
            return
        profile = self.prof_manager.load_profile(profile_id)
        if not profile:
            QMessageBox.critical(self, self.translator.tr('error'),
                                 self.translator.tr('profile_load_error'))
            return
        self.run_import_designer(existing_profile=profile)

    def delete_profile(self):
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_profile_first'))
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('delete_profile_confirm')) == QMessageBox.Yes:
            self.prof_manager.delete_profile(profile_id)
            self.load_profiles()

    def run_import_designer(self, existing_profile=None):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('select_source_dialog_title'))
        dlg.resize(500, 400)
        layout = QVBoxLayout(dlg)

        type_combo = QComboBox()
        type_combo.addItem(self.translator.tr('source_type_file'), SourceType.FILE)
        type_combo.addItem(self.translator.tr('source_type_db'), SourceType.DATABASE)
        type_combo.addItem(self.translator.tr('source_type_url'), SourceType.URL)
        layout.addWidget(type_combo)

        # Группа для файла
        file_group = QGroupBox(self.translator.tr('file_group'))
        file_layout = QVBoxLayout(file_group)
        format_combo = QComboBox()
        for fmt in FileFormat:
            format_combo.addItem(fmt.value, fmt)
        file_layout.addWidget(QLabel(self.translator.tr('file_format_label')))
        file_layout.addWidget(format_combo)
        path_edit = QLineEdit()
        browse_btn = QPushButton(self.translator.tr('browse_button'))
        browse_btn.clicked.connect(lambda: browse_file())
        path_layout = QHBoxLayout()
        path_layout.addWidget(path_edit)
        path_layout.addWidget(browse_btn)
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)

        # Группа для БД
        db_group = QGroupBox(self.translator.tr('db_group'))
        db_layout = QVBoxLayout(db_group)
        db_type_combo = QComboBox()
        db_type_combo.addItems(["postgresql", "mysql", "mssql", "oracle", "sqlite"])
        db_layout.addWidget(QLabel(self.translator.tr('db_type_label')))
        db_layout.addWidget(db_type_combo)

        self.db_host_label = QLabel(self.translator.tr('db_host_label'))
        self.db_host = QLineEdit("localhost")
        self.db_port_label = QLabel(self.translator.tr('db_port_label'))
        self.db_port = QLineEdit()
        self.db_name_label = QLabel(self.translator.tr('db_name_label'))
        self.db_name = QLineEdit()
        self.db_user_label = QLabel(self.translator.tr('db_user_label'))
        self.db_user = QLineEdit()
        self.db_pass_label = QLabel(self.translator.tr('db_pass_label'))
        self.db_pass = QLineEdit()
        self.db_pass.setEchoMode(QLineEdit.Password)

        db_layout.addWidget(self.db_host_label)
        db_layout.addWidget(self.db_host)
        db_layout.addWidget(self.db_port_label)
        db_layout.addWidget(self.db_port)
        db_layout.addWidget(self.db_name_label)
        db_layout.addWidget(self.db_name)
        db_layout.addWidget(self.db_user_label)
        db_layout.addWidget(self.db_user)
        db_layout.addWidget(self.db_pass_label)
        db_layout.addWidget(self.db_pass)

        layout.addWidget(db_group)

        # Группа для URL
        url_group = QGroupBox(self.translator.tr('url_group'))
        url_layout = QVBoxLayout(url_group)
        url_edit = QLineEdit()
        method_combo = QComboBox()
        method_combo.addItems(["GET", "POST"])
        url_layout.addWidget(QLabel(self.translator.tr('url_label')))
        url_layout.addWidget(url_edit)
        url_layout.addWidget(QLabel(self.translator.tr('http_method_label')))
        url_layout.addWidget(method_combo)
        layout.addWidget(url_group)

        def toggle_groups():
            st = type_combo.currentData()
            file_group.setVisible(st == SourceType.FILE)
            db_group.setVisible(st == SourceType.DATABASE)
            url_group.setVisible(st == SourceType.URL)
            if st == SourceType.DATABASE:
                toggle_db_fields()

        def toggle_db_fields():
            is_sqlite = db_type_combo.currentText() == 'sqlite'
            self.db_host_label.setVisible(not is_sqlite)
            self.db_host.setVisible(not is_sqlite)
            self.db_port_label.setVisible(not is_sqlite)
            self.db_port.setVisible(not is_sqlite)
            self.db_user_label.setVisible(not is_sqlite)
            self.db_user.setVisible(not is_sqlite)
            self.db_pass_label.setVisible(not is_sqlite)
            self.db_pass.setVisible(not is_sqlite)
            self.db_name_label.setText("Путь к файлу SQLite:" if is_sqlite else self.translator.tr('db_name_label'))
            if is_sqlite:
                if not hasattr(self, 'browse_db_btn'):
                    self.browse_db_btn = QPushButton("Обзор...")
                    self.browse_db_btn.clicked.connect(browse_db_file)
                    db_layout.insertWidget(db_layout.indexOf(self.db_name) + 1, self.browse_db_btn)
                self.browse_db_btn.setVisible(True)
            else:
                if hasattr(self, 'browse_db_btn'):
                    self.browse_db_btn.setVisible(False)

        def browse_db_file():
            path, _ = QFileDialog.getOpenFileName(dlg, "Выберите файл SQLite")
            if path:
                self.db_name.setText(path)

        def browse_file():
            path, _ = QFileDialog.getOpenFileName(dlg, self.translator.tr('select_file_dialog'))
            if path:
                path_edit.setText(path)

        type_combo.currentIndexChanged.connect(lambda: toggle_groups())
        db_type_combo.currentTextChanged.connect(lambda: toggle_db_fields())
        toggle_groups()

        # Заполнение полей из профиля
        if existing_profile:
            profile = existing_profile
            idx = type_combo.findData(profile.source_type)
            if idx >= 0:
                type_combo.setCurrentIndex(idx)
                toggle_groups()
            if profile.source_type == SourceType.FILE:
                if profile.source_path:
                    path_edit.setText(profile.source_path)
                if profile.file_format:
                    fmt_idx = format_combo.findData(FileFormat(profile.file_format))
                    if fmt_idx >= 0:
                        format_combo.setCurrentIndex(fmt_idx)
            elif profile.source_type == SourceType.DATABASE:
                if profile.db_type:
                    db_idx = db_type_combo.findText(profile.db_type)
                    if db_idx >= 0:
                        db_type_combo.setCurrentIndex(db_idx)
                        toggle_db_fields()
                if profile.db_host: self.db_host.setText(profile.db_host)
                if profile.db_port: self.db_port.setText(str(profile.db_port))
                if profile.db_name: self.db_name.setText(profile.db_name)
                if profile.db_user: self.db_user.setText(profile.db_user)
                if profile.db_pass: self.db_pass.setText(profile.db_pass)
            elif profile.source_type == SourceType.URL:
                if profile.source_path: url_edit.setText(profile.source_path)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        if dlg.exec_() != QDialog.Accepted:
            return

        try:
            st = type_combo.currentData()
            if st == SourceType.FILE:
                connector = FileConnector(path_edit.text(), format_combo.currentData())
            elif st == SourceType.DATABASE:
                params = {
                    'db_type': db_type_combo.currentText(),
                    'host': self.db_host.text(),
                    'port': self.db_port.text() or None,
                    'database': self.db_name.text(),
                    'user': self.db_user.text(),
                    'password': self.db_pass.text()
                }
                connector = DBConnector("", **params)
            else:
                connector = URLConnector(url_edit.text())
            connector.connect()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))
            return

        designer = ImportDesignerV2(self.db, connector, self)
        if existing_profile:
            designer.editing_profile_id = existing_profile.id
            # Восстанавливаем связи после загрузки сцены
            designer.load_profile_links(existing_profile)
        designer.show()
        self.load_profiles()