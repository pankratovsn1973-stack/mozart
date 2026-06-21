# utils/checkable_model.py
# -*- coding: utf-8 -*-

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem


class CheckableFileModel(QStandardItemModel):
    """Модель дерева с ленивой загрузкой и безопасной сквозной рекурсией веток."""
    IGNORE_DIRS = {".venv", "venv", ".git", "__pycache__", ".idea", "build", "dist"}

    def __init__(self, root_path):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.setHorizontalHeaderLabels(["Структура проекта"])
        self._block_signals = False

        root_node = self.invisibleRootItem()
        self._populate_node(self.root_path, root_node)
        self.itemChanged.connect(self._on_item_changed)

    def _populate_node(self, current_path, parent_item):
        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return

        dirs = [i for i in items if os.path.isdir(os.path.join(current_path, i)) and i not in self.IGNORE_DIRS]
        files = [i for i in items if os.path.isfile(os.path.join(current_path, i))]

        for name in dirs + files:
            full_path = os.path.join(current_path, name)
            is_dir = os.path.isdir(full_path)

            name_item = QStandardItem(name)
            name_item.setCheckable(True)
            name_item.setCheckState(Qt.Unchecked)
            name_item.setEditable(False)
            name_item.setData(full_path, Qt.UserRole)
            name_item.setData(False, Qt.UserRole + 1)

            parent_item.appendRow(name_item)
            if is_dir:
                dummy = QStandardItem("loading...")
                dummy.setEditable(False)
                name_item.appendRow(dummy)

    def load_folder_dynamic(self, item):
        """Ленивая подгрузка папки с диска в память."""
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
        state = item.checkState()
        self._set_children_state(item, state)
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

    def get_selected_files(self):
        selected_paths = []
        self._collect_files(self.invisibleRootItem(), selected_paths)
        return selected_paths

    def _collect_files(self, parent_item, paths_list):
        """Сквозной рекурсивный сбор файлов с безопасным раскрытием веток."""
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
                if child.text() == "loading...":
                    continue

                path = child.data(Qt.UserRole)

                # ИБО ИСПРАВЛЕНО: Догружаем только если это ГАЛОЧКА + РЕАЛЬНЫЙ КАТАЛОГ на диске
                if child.checkState() == Qt.Checked and os.path.isdir(path) and not child.data(Qt.UserRole + 1):
                    self.load_folder_dynamic(child)

                if child.checkState() == Qt.Checked:
                    paths_list.append(path)

                if child.rowCount() > 0:
                    self._collect_files(child, paths_list)

    def get_all_checked_nodes(self):
        checked_paths = []
        self._collect_all_checked(self.invisibleRootItem(), checked_paths)
        return checked_paths

    def _collect_all_checked(self, parent_item, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                if child.checkState() == Qt.Checked:
                    paths_list.append(child.data(Qt.UserRole))
                if child.rowCount() > 0:
                    self._collect_all_checked(child, paths_list)

    def restore_checked_nodes(self, checked_paths):
        if not checked_paths:
            return
        self._block_signals = True
        self._apply_restored_states(self.invisibleRootItem(), set(checked_paths))
        self._block_signals = False

    def _apply_restored_states(self, parent_item, checked_set):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                path = child.data(Qt.UserRole)
                if path in checked_set:
                    child.setCheckState(Qt.Checked)
                if child.rowCount() > 0:
                    self._apply_restored_states(child, checked_set)
                    self._update_parent_state(child)
