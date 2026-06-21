# utils/project_packer.py
# -*- coding: utf-8 -*-

import os
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QTreeView, QPushButton, QLineEdit, QLabel,
                               QFileDialog, QStyle, QFrame)
from PySide6.QtCore import Qt, QDir, QModelIndex

# Родные модульные импорты сборщика Mozart
from checkable_model import CheckableFileModel
from db_manager import PackDbManager
from packer_operations import PackerOperations


class ProjectPackerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.project_root = "/home/sergey/Documents/configurate"
        self.setWindowTitle("Сборщик проекта Mozart ERP — Pack Tool")
        self.resize(1000, 600)

        self.db = PackDbManager()
        self.ops = PackerOperations(self.project_root)

        self.setup_ui()
        self.load_state()

    def setup_ui(self):
        main_hbox = QHBoxLayout(self)
        main_hbox.setContentsMargins(10, 10, 10, 10)
        main_hbox.setSpacing(10)

        # СЛЕВА: Дерево проекта (1 колонка)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel(f"<b>Источник данных:</b> {self.project_root}"))

        self.tree_view = QTreeView(self)
        self.model = CheckableFileModel(self.project_root)
        self.tree_view.setModel(self.model)
        self.tree_view.expanded.connect(self._on_node_expanded)
        left_layout.addWidget(self.tree_view)
        main_hbox.addWidget(left_widget, stretch=6)

        # ПОСЕРЕДИНЕ: Черная линия
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("color: #000000; qproperty-lineWidth: 1;")
        main_hbox.addWidget(separator)

        # СПРАВА: Панель настроек
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignTop)

        right_layout.addWidget(QLabel("<b>Каталог назначения:</b>"))
        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)
        self.edt_target_path = QLineEdit(self)
        self.edt_target_path.setReadOnly(True)
        self.edt_target_path.setPlaceholderText("Выберите директорию...")
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

        right_layout.addWidget(QLabel("<b>Имя создаваемого каталога:</b><br><small>(при копировании)</small>"))
        self.edt_folder_name = QLineEdit(self)
        self.edt_folder_name.setText("configurate_package")
        right_layout.addWidget(self.edt_folder_name)

        right_layout.addStretch(1)

        self.btn_json = QPushButton("Создать Mozart.json", self)
        self.btn_json.setStyleSheet(
            "QPushButton { background-color: #f0f0f0; color: #000000; border: 1px solid #ababab; border-radius: 3px; height: 38px; font-weight: bold; } QPushButton:hover { background-color: #e2e2e2; }")
        self.btn_json.clicked.connect(
            lambda: self.ops.export_to_json(self, self.model.get_selected_files(), self.edt_target_path.text().strip()))

        self.btn_copy = QPushButton("Создать структуру каталогов", self)
        self.btn_copy.setStyleSheet(
            "QPushButton { background-color: #f0f0f0; color: #000000; border: 1px solid #ababab; border-radius: 3px; height: 38px; font-weight: bold; } QPushButton:hover { background-color: #e2e2e2; }")
        self.btn_copy.clicked.connect(lambda: self.ops.copy_selected_files(self, self.model.get_selected_files(),
                                                                           self.edt_target_path.text().strip(),
                                                                           self.edt_folder_name.text().strip()))

        right_layout.addWidget(self.btn_json)
        right_layout.addWidget(self.btn_copy)
        main_hbox.addWidget(right_widget, stretch=4)

    def _on_node_expanded(self, index):
        item = self.model.itemFromIndex(index)
        if item:
            self.model.load_folder_dynamic(item)

    def _show_target_browser(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите каталог назначения", QDir.homePath(),
                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dir_path:
            self.edt_target_path.setText(dir_path)

    def _get_expanded_nodes(self):
        expanded_paths = []
        self._collect_expanded(QModelIndex(), expanded_paths)
        return expanded_paths

    def _collect_expanded(self, parent_index, paths_list):
        for row in range(self.model.rowCount(parent_index)):
            index = self.model.index(row, 0, parent_index)
            if self.tree_view.isExpanded(index):
                paths_list.append(self.model.data(index, Qt.UserRole))
                if self.model.hasChildren(index):
                    self._collect_expanded(index, paths_list)

    def _restore_expanded_nodes(self, expanded_paths):
        if not expanded_paths:
            return
        # Очищаем кортежи SQLite в чистые строки
        clean_paths = [p[0] if isinstance(p, tuple) else p for p in expanded_paths]
        expanded_set = set(clean_paths)
        while True:
            if not self._apply_expanded_pass(QModelIndex(), expanded_set):
                break

    def _apply_expanded_pass(self, parent_index, expanded_set):
        added = False
        for row in range(self.model.rowCount(parent_index)):
            index = self.model.index(row, 0, parent_index)
            path = self.model.data(index, Qt.UserRole)
            if path in expanded_set and not self.tree_view.isExpanded(index):
                item = self.model.itemFromIndex(index)
                if item:
                    self.model.load_folder_dynamic(item)
                    self.tree_view.setExpanded(index, True)
                    added = True
            if self.model.hasChildren(index):
                if self._apply_expanded_pass(index, expanded_set):
                    added = True
        return added

    def load_state(self):
        target_path, folder_name, checked_nodes, expanded_nodes = self.db.load_settings()

        # Распаковываем кортежи SQLite в обычные строки
        clean_target = target_path[0] if isinstance(target_path, tuple) else target_path
        clean_folder = folder_name[0] if isinstance(folder_name, tuple) else folder_name

        self.edt_target_path.setText(clean_target)
        self.edt_folder_name.setText(clean_folder)

        self._restore_expanded_nodes(expanded_nodes)

        if checked_nodes:
            # ИСПРАВЛЕНО ЖЕСТКО: Распаковываем кортежи строк из SQLite перед os.path.exists
            clean_checked = [p[0] if isinstance(p, tuple) else p for p in checked_nodes]
            valid_nodes = [p for p in clean_checked if os.path.exists(p)]
            self.model.restore_checked_nodes(valid_nodes)

    def closeEvent(self, event):
        self.db.save_settings(
            self.edt_target_path.text(), self.edt_folder_name.text(),
            self.model.get_all_checked_nodes(), self._get_expanded_nodes()
        )
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    packer = ProjectPackerWidget()
    packer.show()
    sys.exit(app.exec())
