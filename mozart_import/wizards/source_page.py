# -*- coding: utf-8 -*-
# mozart_import/wizards/source_page.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog, QGroupBox, QMessageBox
from lang.local_translator import LocalTranslator
from ..core.models import SourceType, FileFormat
from ..connectors.file_connector import FileConnector
from ..connectors.db_connector import DBConnector
from ..connectors.url_connector import URLConnector


class SourcePage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = LocalTranslator()
        self.setTitle(self.translator.tr('source_page_title'))
        self.setSubTitle(self.translator.tr('source_page_subtitle'))
        layout = QVBoxLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItem(self.translator.tr('source_type_file'), SourceType.FILE)
        self.type_combo.addItem(self.translator.tr('source_type_db'), SourceType.DATABASE)
        self.type_combo.addItem(self.translator.tr('source_type_url'), SourceType.URL)
        self.type_combo.currentIndexChanged.connect(self.toggle_groups)
        layout.addWidget(QLabel(self.translator.tr('source_type_label')))
        layout.addWidget(self.type_combo)

        # Файл
        self.file_group = QGroupBox(self.translator.tr('file_group'))
        file_layout = QVBoxLayout(self.file_group)
        self.format_combo = QComboBox()
        for fmt in [FileFormat.JSON, FileFormat.XML, FileFormat.DBF, FileFormat.CSV, FileFormat.EXCEL]:
            self.format_combo.addItem(fmt.value, fmt)
        file_layout.addWidget(QLabel(self.translator.tr('file_format_label')))
        file_layout.addWidget(self.format_combo)
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton(self.translator.tr('browse_button'))
        self.browse_btn.clicked.connect(self.browse_file)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        file_layout.addLayout(path_layout)
        layout.addWidget(self.file_group)

        # База данных
        self.db_group = QGroupBox(self.translator.tr('db_group'))
        db_layout = QVBoxLayout(self.db_group)
        self.db_type = QComboBox()
        self.db_type.addItems(["postgresql", "mysql", "mssql", "oracle"])
        db_layout.addWidget(QLabel(self.translator.tr('db_type_label')))
        db_layout.addWidget(self.db_type)
        self.db_host = QLineEdit("localhost")
        self.db_port = QLineEdit()
        self.db_name = QLineEdit()
        self.db_user = QLineEdit()
        self.db_pass = QLineEdit()
        self.db_pass.setEchoMode(QLineEdit.Password)
        db_layout.addWidget(QLabel(self.translator.tr('db_host_label')))
        db_layout.addWidget(self.db_host)
        db_layout.addWidget(QLabel(self.translator.tr('db_port_label')))
        db_layout.addWidget(self.db_port)
        db_layout.addWidget(QLabel(self.translator.tr('db_name_label')))
        db_layout.addWidget(self.db_name)
        db_layout.addWidget(QLabel(self.translator.tr('db_user_label')))
        db_layout.addWidget(self.db_user)
        db_layout.addWidget(QLabel(self.translator.tr('db_pass_label')))
        db_layout.addWidget(self.db_pass)
        layout.addWidget(self.db_group)

        # URL
        self.url_group = QGroupBox(self.translator.tr('url_group'))
        url_layout = QVBoxLayout(self.url_group)
        self.url_edit = QLineEdit()
        url_layout.addWidget(QLabel(self.translator.tr('url_label')))
        url_layout.addWidget(self.url_edit)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        url_layout.addWidget(QLabel(self.translator.tr('http_method_label')))
        url_layout.addWidget(self.method_combo)
        layout.addWidget(self.url_group)

        layout.addStretch()
        self.toggle_groups()

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('source_page_title'))
        self.setSubTitle(self.translator.tr('source_page_subtitle'))
        self.type_combo.setItemText(0, self.translator.tr('source_type_file'))
        self.type_combo.setItemText(1, self.translator.tr('source_type_db'))
        self.type_combo.setItemText(2, self.translator.tr('source_type_url'))
        self.file_group.setTitle(self.translator.tr('file_group'))
        self.browse_btn.setText(self.translator.tr('browse_button'))
        self.db_group.setTitle(self.translator.tr('db_group'))
        self.url_group.setTitle(self.translator.tr('url_group'))

    def toggle_groups(self):
        st = self.type_combo.currentData()
        self.file_group.setVisible(st == SourceType.FILE)
        self.db_group.setVisible(st == SourceType.DATABASE)
        self.url_group.setVisible(st == SourceType.URL)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.translator.tr('select_file_dialog'))
        if path:
            self.path_edit.setText(path)

    def validatePage(self):
        st = self.type_combo.currentData()
        try:
            if st == SourceType.FILE:
                self.wizard.connector = FileConnector(self.path_edit.text(), self.format_combo.currentData())
            elif st == SourceType.DATABASE:
                params = {
                    'db_type': self.db_type.currentText(),
                    'host': self.db_host.text(),
                    'port': self.db_port.text() or None,
                    'database': self.db_name.text(),
                    'user': self.db_user.text(),
                    'password': self.db_pass.text()
                }
                self.wizard.connector = DBConnector("", **params)
            else:
                self.wizard.connector = URLConnector(self.url_edit.text())
            self.wizard.connector.connect()
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))
            return False