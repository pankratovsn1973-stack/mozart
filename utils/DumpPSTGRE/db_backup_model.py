# utils/db_backup_model.py
# -- coding: utf-8 --
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
            # 1. Узел Схемы
            schema_item = QStandardItem(f"Схема: {schema_name}")
            schema_item.setCheckable(True)
            schema_item.setEditable(False)
            schema_item.setData({
                "type": "schema",
                "name": schema_name,
                "comment": schema_data["description"]
            }, Qt.UserRole)
            parent_node.appendRow(schema_item)

            # Опции схемы
            for key, label in [
                ("export_schema_desc", "Описание схемы"),
                ("export_triggers", "Выгружать триггеры"),
                ("export_rules", "Выгружать правила"),
                ("export_keys", "Выгружать ключи")
            ]:
                opt = QStandardItem(label)
                opt.setData({"type": "schema_opt", "key": key, "schema": schema_name}, Qt.UserRole)
                opt.setCheckable(True)
                opt.setEditable(False)
                schema_item.appendRow(opt)

            # 2. Таблицы
            if schema_data.get("tables"):
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

                    for p_key, p_label in [("description", "Описание"), ("structure", "Структура"), ("data", "Данные")]:
                        prop = QStandardItem(p_label)
                        prop.setData({"type": "table_opt", "key": p_key, "table": t_name, "schema": schema_name},
                                     Qt.UserRole)
                        prop.setCheckable(True)
                        prop.setEditable(False)
                        t_item.appendRow(prop)

            # 3. Функции
            if schema_data.get("functions"):
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

            # 4. Вьюхи
            if schema_data.get("views"):
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
        """Каскадный пересчет при ручном изменении."""
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
                cs = child.checkState()
                if cs == Qt.Checked:
                    all_unchecked = False
                elif cs == Qt.Unchecked:
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
        """
        Полное восстановление состояния из БД.
        Сначала снимает ВСЕ галочки, затем ставит только те, что есть в базе.
        """
        self._block_signals = True

        # ШАГ 1: Полный сброс всего дерева
        self._clear_all_checkstates(self.invisibleRootItem())

        # ШАГ 2: Установка галочек из базы
        if checked_paths:
            self._apply_restored_states(self.invisibleRootItem(), "", set(checked_paths))

        # ШАГ 3: Пересчет родителей (PartiallyChecked)
        self._recalculate_parents(self.invisibleRootItem())

        self._block_signals = False

    def _clear_all_checkstates(self, parent_item):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
                child.setCheckState(Qt.Unchecked)
                if child.rowCount() > 0:
                    self._clear_all_checkstates(child)

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

    def _recalculate_parents(self, parent_item):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.rowCount() > 0:
                self._recalculate_parents(child)
                self._update_parent_state(child)