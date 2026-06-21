# utils/db_backup_tool.py
# -*- coding: utf-8 -*-

import os
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QTreeView, QPushButton, QLineEdit, QLabel,
                               QFileDialog, QMessageBox, QStyle, QFrame)
from PySide6.QtCore import Qt, QDir, QModelIndex

# Родные модульные импорты бэкапа Mozart ERP
from db_backup_extractor import DbBackupExtractor
from db_backup_model import DbBackupModel
from db_backup_sqlite import BackupDbManager


class DbBackupToolWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "mozart_erp",
            "user": "postgres",
            "password": "SQLSerIra!"
        }

        self.setWindowTitle("Инспектор бэкапа СУБД — Mozart ERP Backup")
        self.resize(1100, 650)

        self.db_sqlite = BackupDbManager()
        self.extractor = DbBackupExtractor(self.db_config)
        self.db_structure = self.extractor.fetch_db_structure()

        self.setup_ui()
        self.load_state()

    def setup_ui(self):
        main_hbox = QHBoxLayout(self)
        main_hbox.setContentsMargins(10, 10, 10, 10)
        main_hbox.setSpacing(10)

        # СЛЕВА: Дерево объектов БД
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("<b>Объекты и опции схемы PostgreSQL:</b>"))

        self.tree_view = QTreeView(self)
        self.model = DbBackupModel(self.db_structure)
        self.tree_view.setModel(self.model)
        self.tree_view.expandToDepth(0)
        left_layout.addWidget(self.tree_view)
        main_hbox.addWidget(left_widget, stretch=6)

        # ПОСЕРЕДИНЕ: Черный разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("color: #000000; qproperty-lineWidth: 1;")
        main_hbox.addWidget(separator)

        # СПРАВА: Настройки
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignTop)

        right_layout.addWidget(QLabel("<b>Каталог сохранения дампа:</b>"))
        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)

        self.edt_target_path = QLineEdit(self)
        self.edt_target_path.setReadOnly(True)
        self.edt_target_path.setPlaceholderText("Выберите директорию на диске...")
        path_layout.addWidget(self.edt_target_path)

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btn_browse.clicked.connect(self._show_target_browser)
        path_layout.addWidget(self.btn_browse)

        self.btn_clear = QPushButton(self)
        self.btn_clear.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.btn_clear.clicked.connect(lambda: self.edt_target_path.clear())
        path_layout.addWidget(self.btn_clear)
        right_layout.addLayout(path_layout)

        right_layout.addWidget(QLabel("<b>Имя файла резервной копии (.sql):</b>"))
        self.edt_file_name = QLineEdit(self)
        self.edt_file_name.setText("mozart_dump.sql")
        right_layout.addWidget(self.edt_file_name)

        right_layout.addStretch(1)

        self.btn_run_dump = QPushButton("Запустить выгрузку дампа", self)
        self.btn_run_dump.setStyleSheet("""
            QPushButton { background-color: #f0f0f0; color: #000000; border: 1px solid #ababab; border-radius: 3px; height: 40px; font-weight: bold; }
            QPushButton:hover { background-color: #e2e2e2; }
        """)
        self.btn_run_dump.clicked.connect(self.run_backup_process)
        right_layout.addWidget(self.btn_run_dump)

        main_hbox.addWidget(right_widget, stretch=4)

    def _show_target_browser(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите каталог назначения", QDir.homePath(),
                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dir_path:
            self.edt_target_path.setText(dir_path)

    def _parse_tree_config(self):
        config = {}
        root = self.model.invisibleRootItem()
        for s_idx in range(root.rowCount()):
            s_item = root.child(s_idx, 0)
            s_data = s_item.data(Qt.UserRole)
            s_name = s_data["name"]

            config[s_name] = {
                "schema_comment": s_data["comment"], "export_schema_desc": False,
                "export_triggers": False, "export_rules": False, "export_keys": False,
                "tables": {}, "functions": {}, "views": []
            }

            for c_idx in range(s_item.rowCount()):
                child = s_item.child(c_idx, 0)
                c_data = child.data(Qt.UserRole)

                if c_data["type"] == "schema_opt" and child.checkState() == Qt.Checked:
                    config[s_name][c_data["key"]] = True

                elif c_data["type"] == "group" and c_data["name"] == "tables":
                    for t_idx in range(child.rowCount()):
                        t_item = child.child(t_idx, 0)
                        t_data = t_item.data(Qt.UserRole)
                        t_name = t_data["name"]

                        t_cfg = {"description": False, "structure": False, "data": False}
                        for p_idx in range(t_item.rowCount()):
                            p_item = t_item.child(p_idx, 0)
                            p_data = p_item.data(Qt.UserRole)
                            if p_item.checkState() == Qt.Checked:
                                t_cfg[p_data["key"]] = True
                        if any(t_cfg.values()):
                            config[s_name]["tables"][t_name] = t_cfg

                elif c_data["type"] == "group" and c_data["name"] == "functions":
                    for f_idx in range(child.rowCount()):
                        f_item = child.child(f_idx, 0)
                        f_data = f_item.data(Qt.UserRole)
                        if f_item.checkState() == Qt.Checked:
                            config[s_name]["functions"][f_data["identity"]] = f_data["name"]

                elif c_data["type"] == "group" and c_data["name"] == "views":
                    for v_idx in range(child.rowCount()):
                        v_item = child.child(v_idx, 0)
                        v_data = v_item.data(Qt.UserRole)
                        if v_item.checkState() == Qt.Checked:
                            config[s_name]["views"].append(v_data["name"])
        return config

    def run_backup_process(self):
        target_dir = self.edt_target_path.text().strip()
        file_name = self.edt_file_name.text().strip()
        if not target_dir or not file_name:
            QMessageBox.warning(self, "Внимание", "Укажите каталог сохранения и имя файла .sql!")
            return

        dump_config = self._parse_tree_config()
        full_sql_path = os.path.join(target_dir, file_name)

        success, msg = self.extractor.generate_dump(full_sql_path, dump_config)
        if success:
            QMessageBox.information(self, "Успех", f"{msg}\nФайл: {full_sql_path}")
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def load_state(self):
        target_path, file_name, checked_nodes = self.db_sqlite.load_settings()
        self.edt_target_path.setText(target_path if not isinstance(target_path, tuple) else target_path)
        self.edt_file_name.setText(file_name if not isinstance(file_name, tuple) else file_name)
        if checked_nodes:
            clean_checked = [p if isinstance(p, tuple) else p for p in checked_nodes]
            self.model.restore_checked_nodes(clean_checked)

    def closeEvent(self, event):
        self.db_sqlite.save_settings(
            self.edt_target_path.text(), self.edt_file_name.text(),
            self.model.get_all_checked_nodes()
        )
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = DbBackupToolWidget()
    tool.show()
    sys.exit(app.exec())
