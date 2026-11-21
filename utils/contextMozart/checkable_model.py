# utils/contextMozart/checkable_model.py
# -*- coding: utf-8 -*-
"""
Модель дерева проекта с чекбоксами и ленивой загрузкой.
Адаптация CheckableFileModel из utils/dmppython/project_packer.py,
но с поддержкой передачи списка выбранных файлов в ContextConfig.
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem


class CheckableContextModel(QStandardItemModel):
    """Дерево файлов проекта с чекбоксами."""

    IGNORE_DIRS = {
        '.venv', 'venv', 'env', '.env',
        '__pycache__', '.git', '.svn', '.hg',
        '.idea', '.vscode', 'node_modules',
        'build', 'dist', '.pytest_cache', '.mypy_cache', '.tox',
        'backups', 'music_pool', 'forms', 'output', 'lang_data',
    }

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.setHorizontalHeaderLabels(["Структура проекта"])
        self._block_signals = False
        self.saved_checked_paths = set()

        if os.path.exists(self.root_path):
            self._populate_node(self.root_path, self.invisibleRootItem())
        self.itemChanged.connect(self._on_item_changed)

    def set_saved_checked_paths(self, paths):
        self.saved_checked_paths = set(paths)
        self._apply_checks_to_visible(self.invisibleRootItem())

    def _apply_checks_to_visible(self, parent_item):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                path = child.data(Qt.UserRole)
                if path in self.saved_checked_paths:
                    child.setCheckState(Qt.Checked)
                    self._update_parent_state(child)
                if child.rowCount() > 0:
                    self._apply_checks_to_visible(child)

    def _populate_node(self, current_path, parent_item):
        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return
        dirs = [i for i in items
                if os.path.isdir(os.path.join(current_path, i))
                and i not in self.IGNORE_DIRS]
        files = [i for i in items
                 if os.path.isfile(os.path.join(current_path, i))
                 and i.endswith('.py')]

        for name in dirs + files:
            full_path = os.path.join(current_path, name)
            is_dir = os.path.isdir(full_path)

            name_item = QStandardItem(name)
            name_item.setCheckable(True)
            name_item.setEditable(False)
            name_item.setData(full_path, Qt.UserRole)
            name_item.setData(False, Qt.UserRole + 1)

            if full_path in self.saved_checked_paths:
                name_item.setCheckState(Qt.Checked)
            else:
                name_item.setCheckState(Qt.Unchecked)

            parent_item.appendRow(name_item)

            if is_dir:
                dummy = QStandardItem("loading...")
                dummy.setEditable(False)
                name_item.appendRow(dummy)

    def load_folder_dynamic(self, item):
        if not item or item.data(Qt.UserRole + 1) or item.text() == "loading...":
            return
        item.setData(True, Qt.UserRole + 1)
        if item.rowCount() > 0 and item.child(0).text() == "loading...":
            item.removeRow(0)

        full_path = item.data(Qt.UserRole)
        self._block_signals = True
        self._populate_node(full_path, item)
        if item.checkState() == Qt.Checked:
            self._set_children_state(item, Qt.Checked)
        self._block_signals = False

    def _on_item_changed(self, item):
        if self._block_signals:
            return
        self._block_signals = True
        self._set_children_state(item, item.checkState())
        self._update_parent_state(item)
        self._block_signals = False

    def _set_children_state(self, parent_item, state):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                child.setCheckState(state)
                if child.rowCount() > 0:
                    self._set_children_state(child, state)

    def _update_parent_state(self, item):
        parent = item.parent()
        if not parent:
            return
        all_checked, all_unchecked = True, True
        for row in range(parent.rowCount()):
            child = parent.child(row, 0)
            if child and child.text() != "loading...":
                if child.checkState() == Qt.Checked:
                    all_unchecked = False
                elif child.checkState() == Qt.Unchecked:
                    all_checked = False
                else:
                    all_checked = all_unchecked = False
        if all_checked:
            parent.setCheckState(Qt.Checked)
        elif all_unchecked:
            parent.setCheckState(Qt.Unchecked)
        else:
            parent.setCheckState(Qt.PartiallyChecked)
        self._update_parent_state(parent)

    def get_selected_py_files(self) -> list:
        """Возвращает список выбранных .py файлов (полные пути)."""
        result = []
        self._collect_py_files(self.invisibleRootItem(), result)
        return result

    def _collect_py_files(self, parent_item, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                path = child.data(Qt.UserRole)
                if child.checkState() == Qt.Checked:
                    if os.path.isfile(path) and path.endswith('.py'):
                        paths_list.append(path)
                    elif os.path.isdir(path) and not child.data(Qt.UserRole + 1):
                        self.load_folder_dynamic(child)
                        self._collect_py_files(child, paths_list)
                elif child.rowCount() > 0:
                    self._collect_py_files(child, paths_list)

    def get_all_checked_nodes(self) -> list:
        checked = []
        self._collect_all_checked(self.invisibleRootItem(), checked)
        return checked

    def _collect_all_checked(self, parent_item, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                if child.checkState() == Qt.Checked:
                    paths_list.append(child.data(Qt.UserRole))
                if child.rowCount() > 0:
                    self._collect_all_checked(child, paths_list)