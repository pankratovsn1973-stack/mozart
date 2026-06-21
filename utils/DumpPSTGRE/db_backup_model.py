# utils/db_backup_model.py
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem


class DbBackupModel(QStandardItemModel):
    """Кастомная модель дерева для управления каскадными чекбоксами объектов СУБД."""

    def __init__(self, db_structure):
        super().__init__()
        self.setHorizontalHeaderLabels(["Объекты базы данных"])
        self._block_signals = False

        root_node = self.invisibleRootItem()
        self._build_tree(db_structure, root_node)
        self.itemChanged.connect(self._on_item_changed)

    def _build_tree(self, db_structure, parent_node):
        """Динамическое построение дерева объектов на основе метаданных СУБД."""
        for schema_name, schema_data in sorted(db_structure.items()):
            # 1. Узел Схемы (Верхний уровень)
            schema_item = QStandardItem(f"Схема: {schema_name}")
            schema_item.setCheckable(True)
            schema_item.setEditable(False)
            schema_item.setData({"type": "schema", "name": schema_name, "comment": schema_data["description"]},
                                Qt.UserRole)
            parent_node.appendRow(schema_item)

            # 1.1 Параметры/Опции внутри самой схемы
            opt_desc = QStandardItem("Описание схемы")
            opt_desc.setData({"type": "schema_opt", "key": "export_schema_desc", "schema": schema_name}, Qt.UserRole)

            opt_trig = QStandardItem("Выгружать триггеры")
            opt_trig.setData({"type": "schema_opt", "key": "export_triggers", "schema": schema_name}, Qt.UserRole)

            opt_rules = QStandardItem("Выгружать правила")
            opt_rules.setData({"type": "schema_opt", "key": "export_rules", "schema": schema_name}, Qt.UserRole)

            opt_keys = QStandardItem("Выгружать ключи")
            opt_keys.setData({"type": "schema_opt", "key": "export_keys", "schema": schema_name}, Qt.UserRole)

            for opt in [opt_desc, opt_trig, opt_rules, opt_keys]:
                opt.setCheckable(True)
                opt.setEditable(False)
                schema_item.appendRow(opt)

            # 2. Агрегат "Таблицы" внутри схемы
            if schema_data["tables"]:
                tables_root = QStandardItem("Таблицы")
                tables_root.setCheckable(True)
                tables_root.setEditable(False)
                tables_root.setData({"type": "group", "name": "tables", "schema": schema_name}, Qt.UserRole)
                schema_item.appendRow(tables_root)

                for t_name in sorted(schema_data["tables"].keys()):
                    t_item = QStandardItem(t_name)
                    t_item.setCheckable(True)
                    t_item.setEditable(False)
                    t_item.setData({"type": "table", "name": t_name, "schema": schema_name}, Qt.UserRole)
                    tables_root.appendRow(t_item)

                    # Свойства каждой конкретной таблицы
                    p_desc = QStandardItem("Описание")
                    p_desc.setData({"type": "table_opt", "key": "description", "table": t_name, "schema": schema_name},
                                   Qt.UserRole)

                    p_struct = QStandardItem("Структура")
                    p_struct.setData({"type": "table_opt", "key": "structure", "table": t_name, "schema": schema_name},
                                     Qt.UserRole)

                    p_data = QStandardItem("Данные")
                    p_data.setData({"type": "table_opt", "key": "data", "table": t_name, "schema": schema_name},
                                   Qt.UserRole)

                    for prop in [p_desc, p_struct, p_data]:
                        prop.setCheckable(True)
                        prop.setEditable(False)
                        t_item.appendRow(prop)

            # 3. Агрегат "Хранимые процедуры" внутри схемы
            if schema_data["functions"]:
                funcs_root = QStandardItem("Хранимые процедуры")
                funcs_root.setCheckable(True)
                funcs_root.setEditable(False)
                funcs_root.setData({"type": "group", "name": "functions", "schema": schema_name}, Qt.UserRole)
                schema_item.appendRow(funcs_root)

                for f_identity, f_name in sorted(schema_data["functions"].items()):
                    f_item = QStandardItem(f_identity)
                    f_item.setCheckable(True)
                    f_item.setEditable(False)
                    f_item.setData({"type": "function", "identity": f_identity, "name": f_name, "schema": schema_name},
                                   Qt.UserRole)
                    funcs_root.appendRow(f_item)

            # 4. Агрегат "Вьюхи" внутри схемы
            if schema_data["views"]:
                views_root = QStandardItem("Вьюхи")
                views_root.setCheckable(True)
                views_root.setEditable(False)
                views_root.setData({"type": "group", "name": "views", "schema": schema_name}, Qt.UserRole)
                schema_item.appendRow(views_root)

                for v_name in sorted(schema_data["views"].keys()):
                    v_item = QStandardItem(v_name)
                    v_item.setCheckable(True)
                    v_item.setEditable(False)
                    v_item.setData({"type": "view", "name": v_name, "schema": schema_name}, Qt.UserRole)
                    views_root.appendRow(v_item)

    def _on_item_changed(self, item):
        """Сквозной каскадный пересчет состояний чекбоксов при клике."""
        if self._block_signals:
            return

        self._block_signals = True
        state = item.checkState()

        # 1. Проброс состояния вниз ко всем детям (наследование галок)
        self._set_children_state(item, state)

        # 2. Каскадный пересчет состояний родителей вверх по цепочке
        self._update_parent_state(item)

        self._block_signals = False

    def _set_children_state(self, parent_item, state):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
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
            if child:
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

    def get_all_checked_nodes(self):
        """Собирает внутренние идентификаторы всех отмеченных узлов для хранения в БД."""
        checked_paths = []
        self._collect_all_checked(self.invisibleRootItem(), "", checked_paths)
        return checked_paths

    def _collect_all_checked(self, parent_item, current_path, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
                node_text = child.text()
                node_path = f"{current_path}/{node_text}" if current_path else node_text
                if child.checkState() == Qt.Checked:
                    paths_list.append(node_path)
                if child.rowCount() > 0:
                    self._collect_all_checked(child, node_path, paths_list)

    def restore_checked_nodes(self, checked_paths):
        """Восстановление состояния чекбоксов по сохраненным текстовым путям."""
        if not checked_paths:
            return
        self._block_signals = True
        self._apply_restored_states(self.invisibleRootItem(), "", set(checked_paths))
        self._block_signals = False

    def _apply_restored_states(self, parent_item, current_path, checked_set):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
                node_text = child.text()
                node_path = f"{current_path}/{node_text}" if current_path else node_text
                if node_path in checked_set:
                    child.setCheckState(Qt.Checked)
                if child.rowCount() > 0:
                    self._apply_restored_states(child, node_path, checked_set)
                    self._update_parent_state(child)
