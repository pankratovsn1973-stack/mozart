# ide_ui_panels.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс-примесь MozartIDEPanelsMixin.
Содержит визуальную разметку панелей главного окна, методы подключения СУБД и вызов окон.
Вынесен из ide_main.py для соблюдения лимита атомизации файлов до 300 строк.
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton,
                               QFrame, QFormLayout, QLineEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt
from ide_core import goProject
from ide_db_work import DBWorkDialog
from database import DatabaseService


class MozartIDEPanelsMixin:
    """Миксин для изоляции UI-компонентов панелей управления и связей с Postgres."""

    def retranslate_ui(self):
        """Динамическая смена языковых меток во всем приложении."""
        self.setWindowTitle(self.translator.tr('window_title_main'))

        # Левая панель
        self.file_group.setTitle(self.translator.tr('group_project_file'))
        self.conn_group.setTitle(self.translator.tr('group_db_connection'))
        self.btn_open.setText(self.translator.tr('btn_open_project'))
        self.btn_new.setText(self.translator.tr('btn_new_project'))
        self.btn_save.setText(self.translator.tr('btn_save_project'))
        self.btn_connect.setText(self.translator.tr('btn_connect'))
        if getattr(goProject, 'db_conn', False):
            self.lbl_conn_status.setText(self.translator.tr('status_connected'))
        else:
            self.lbl_conn_status.setText(self.translator.tr('status_disconnected'))

        # Правая панель
        self.db_group.setTitle(self.translator.tr('group_db_work'))
        self.srv_group.setTitle(self.translator.tr('group_server'))
        self.client_group.setTitle(self.translator.tr('group_client'))
        self.btn_db_work.setText(self.translator.tr('btn_db_work'))
        self.btn_srv_start.setText(self.translator.tr('btn_start_server'))
        self.btn_srv_stop.setText(self.translator.tr('btn_stop_server'))
        self.btn_client_start.setText(self.translator.tr('btn_start_client'))

        # Меню
        self.actions['file_menu'].setTitle(self.translator.tr('menu_file'))
        self.actions['new_project'].setText(self.translator.tr('action_new_project'))
        self.actions['open_project'].setText(self.translator.tr('action_open_project'))
        self.actions['save_project'].setText(self.translator.tr('action_save_project'))
        self.actions['exit'].setText(self.translator.tr('action_exit'))

        self.actions['lang_menu'].setTitle(self.translator.tr('menu_language'))
        self.actions['help_menu'].setTitle(self.translator.tr('menu_help'))
        self.actions['about'].setText(self.translator.tr('action_about'))

        # Статус бар
        self.statusBar.showMessage(self.translator.tr('status_ready'))

    def _create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop)

        # Группа "Файл проекта"
        self.file_group = QGroupBox(self.translator.tr('group_project_file'))
        file_layout = QVBoxLayout()
        self.btn_open = QPushButton()
        self.btn_open.clicked.connect(self.open_project)
        self.btn_new = QPushButton()
        self.btn_new.clicked.connect(self.new_project)
        self.btn_save = QPushButton()
        self.btn_save.clicked.connect(self.save_project)
        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.btn_new)
        file_layout.addWidget(self.btn_save)
        self.file_group.setLayout(file_layout)
        layout.addWidget(self.file_group)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Группа "Подключение к базе данных"
        self.conn_group = QGroupBox(self.translator.tr('group_db_connection'))
        form = QFormLayout()
        self.edit_host = QLineEdit()
        self.edit_port = QLineEdit("5432")
        self.edit_db = QLineEdit()
        self.edit_user = QLineEdit()
        self.edit_pass = QLineEdit()
        self.edit_pass.setEchoMode(QLineEdit.Password)

        form.addRow(self.translator.tr('field_host'), self.edit_host)
        form.addRow(self.translator.tr('field_port'), self.edit_port)
        form.addRow(self.translator.tr('field_db'), self.edit_db)
        form.addRow(self.translator.tr('field_user'), self.edit_user)
        form.addRow(self.translator.tr('field_password'), self.edit_pass)

        self.btn_connect = QPushButton(self.translator.tr('btn_connect'))
        self.btn_connect.clicked.connect(self.connect_to_db)
        self.btn_connect.setEnabled(False)

        form.addRow(self.btn_connect)
        self.conn_group.setLayout(form)
        layout.addWidget(self.conn_group)

        # Информация о статусе подключения
        self.lbl_conn_status = QLabel(self.translator.tr('status_disconnected'))
        self.lbl_conn_status.setStyleSheet("color: red;")
        layout.addWidget(self.lbl_conn_status)

        layout.addStretch()
        return panel

    def _create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop)

        # Группа "Работа с БД"
        self.db_group = QGroupBox(self.translator.tr('group_db_work'))
        db_layout = QVBoxLayout()
        self.btn_db_work = QPushButton(self.translator.tr('btn_db_work'))
        self.btn_db_work.clicked.connect(self.open_db_work)
        self.btn_db_work.setEnabled(False)
        db_layout.addWidget(self.btn_db_work)
        self.db_group.setLayout(db_layout)
        layout.addWidget(self.db_group)

        # Группа "Сервер приложений"
        self.srv_group = QGroupBox(self.translator.tr('group_server'))
        srv_layout = QVBoxLayout()
        self.btn_srv_start = QPushButton(self.translator.tr('btn_start_server'))
        self.btn_srv_stop = QPushButton(self.translator.tr('btn_stop_server'))
        self.btn_srv_start.setEnabled(False)
        self.btn_srv_stop.setEnabled(False)
        srv_layout.addWidget(self.btn_srv_start)
        srv_layout.addWidget(self.btn_srv_stop)
        self.srv_group.setLayout(srv_layout)
        layout.addWidget(self.srv_group)

        # Группа "Клиент"
        self.client_group = QGroupBox(self.translator.tr('group_client'))
        client_layout = QVBoxLayout()
        self.btn_client_start = QPushButton(self.translator.tr('btn_start_client'))
        self.btn_client_start.setEnabled(False)
        client_layout.addWidget(self.btn_client_start)
        self.client_group.setLayout(client_layout)
        layout.addWidget(self.client_group)

        layout.addStretch()
        return panel

    def _update_connection_fields(self):
        """Заполнение полей ввода из структуры goProject."""
        self.edit_host.setText(goProject.db_host)
        self.edit_port.setText(str(goProject.db_port))
        self.edit_db.setText(goProject.db_name)
        self.edit_user.setText(goProject.db_user)
        self.edit_pass.setText(goProject.db_pass)

    def _clear_connection_fields(self):
        self.edit_host.clear()
        self.edit_port.setText("5432")
        self.edit_db.clear()
        self.edit_user.clear()
        self.edit_pass.clear()

    def connect_to_db(self):
        """Установка соединения с СУБД Postgres и синхронизация словарей."""
        goProject.db_host = self.edit_host.text().strip()
        goProject.db_port = self.edit_port.text().strip()
        goProject.db_name = self.edit_db.text().strip()
        goProject.db_user = self.edit_user.text().strip()
        goProject.db_pass = self.edit_pass.text()

        ok, msg = goProject.p_Connect()
        if ok:
            db_service = DatabaseService()
            self.translator.sync_from_postgres(db_service)
            self.retranslate_ui()

            self.lbl_conn_status.setText(self.translator.tr('status_connected'))
            self.lbl_conn_status.setStyleSheet("color: green;")
            self.statusBar.showMessage(self.translator.tr('status_connected'))
            self.btn_db_work.setEnabled(True)
            self.btn_srv_start.setEnabled(True)
            self.btn_client_start.setEnabled(True)
        else:
            self.lbl_conn_status.setText(self.translator.tr('status_disconnected'))
            self.lbl_conn_status.setStyleSheet("color: red;")
            QMessageBox.warning(self, self.translator.tr('error'), msg)
            self.btn_db_work.setEnabled(False)
            self.btn_srv_start.setEnabled(False)
            self.btn_client_start.setEnabled(False)

    def open_db_work(self):
        """Открытие диалога управления сущностями Mozart ERP."""
        if self.db_work_dialog is None or not self.db_work_dialog.isVisible():
            self.db_work_dialog = DBWorkDialog(self)
        self.db_work_dialog.show()
        self.db_work_dialog.raise_()
        self.db_work_dialog.activateWindow()

    def about(self):
        """Окно информации о конфигураторе."""
        QMessageBox.about(self, self.translator.tr('action_about'),
                          "MOZART ERP Configurator\nВерсия 0.1\nРазработано на PySide6")
