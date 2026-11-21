# -*- coding: utf-8 -*-
# dialogs/select_container_dialog.py
"""
Диалог выбора контейнера для перепривязки элемента.

v7.2: работает строго по idCol.
  - Принимает element_id_col текущего элемента.
  - Исключает из списка сам элемент и всех его потомков (по idCol).
  - Возвращает idCol выбранного контейнера.
"""
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt

from ide_core import goProject


CONTAINER_ICONS = {
    'container': '📁',
    'tabcontainer': '📑',
    'group': '📦',
}


class SelectContainerDialog(QDialog):
    """
    Диалог выбора контейнера.

    Параметры:
        collection — CollectionManager
        element_id_col — idCol текущего элемента (исключается из списка вместе с потомками)
    """

    def __init__(self, parent=None, collection=None, element_id_col: int = -1):
        super().__init__(parent)
        self.collection = collection
        self.element_id_col = element_id_col
        self.selected_id_col: Optional[int] = None

        self.setWindowTitle("Включить в контейнер")
        self.resize(500, 550)

        self._setup_ui()
        self._load_tree()

    # =====================================================================
    # UI
    # =====================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Выберите контейнер, в который нужно включить объект.\n"
            "Контейнеры — это <b>container</b>, <b>tabcontainer</b>, <b>group</b>."
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 6px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Контейнер", "Тип", "idCol"])
        self.tree.setColumnWidth(0, 280)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 80)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, 1)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.lbl_status)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText("Включить")
        btn_box.button(QDialogButtonBox.Ok).setEnabled(False)
        btn_box.button(QDialogButtonBox.Cancel).setText("Отмена")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        self.btn_ok = btn_box.button(QDialogButtonBox.Ok)
        layout.addWidget(btn_box)

        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

    # =====================================================================
    # Загрузка дерева (по idCol)
    # =====================================================================
    def _load_tree(self):
        self.tree.clear()
        if self.collection is None:
            self.lbl_status.setText("Коллекция не передана")
            return

        elements = self.collection._elements

        # Собираем idCol потомков текущего элемента (для защиты от цикла)
        excluded_idcols = self._collect_excluded_idcols(elements, self.element_id_col)

        # idCol → QTreeWidgetItem
        items_map: Dict[int, QTreeWidgetItem] = {}

        for eid, elem in elements.items():
            elem_idcol = elem.get('id_col', 0)
            if elem_idcol in excluded_idcols:
                continue

            cclass = str(elem.get('cclass', '')).lower()
            is_logical = elem.get('is_logical', False)
            parent_id = elem.get('parent_id')

            is_container = cclass in CONTAINER_ICONS and not is_logical
            is_root = (parent_id is None)

            if not (is_container or is_root):
                continue

            if is_root:
                icon = '🏠'
                display = f"🏠 Корень сцены (ic={elem_idcol})"
                cclass_display = 'root'
            else:
                icon = CONTAINER_ICONS.get(cclass, '📁')
                calias = elem.get('calias', '') or f'id={eid}'
                display = f"{icon} {calias} (ic={elem_idcol})"
                cclass_display = cclass

            item = QTreeWidgetItem()
            item.setText(0, display)
            item.setText(1, cclass_display)
            item.setText(2, str(elem_idcol))
            item.setData(0, Qt.UserRole, elem_idcol)
            item.setData(0, Qt.UserRole + 1, 'root' if is_root else 'container')

            if is_root:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setForeground(0, Qt.gray)

            items_map[elem_idcol] = item

        # Иерархия
        for elem_idcol, item in items_map.items():
            # Ищем элемент по idCol, чтобы узнать parent_id
            elem = self.collection.get_element_by_id_col(elem_idcol)
            if elem is None:
                continue
            parent_id = elem.get('parent_id')
            if parent_id is not None:
                parent_elem = elements.get(parent_id)
                if parent_elem:
                    parent_idcol = parent_elem.get('id_col')
                    if parent_idcol in items_map:
                        items_map[parent_idcol].addChild(item)
                        continue
            self.tree.addTopLevelItem(item)

        self.tree.expandAll()

        selectable_count = sum(
            1 for ic, item in items_map.items()
            if item.data(0, Qt.UserRole + 1) == 'container'
        )
        if selectable_count == 0:
            self.lbl_status.setText(
                "Нет доступных контейнеров для включения. "
                "Создайте container, tabcontainer или group."
            )
        else:
            self.lbl_status.setText(f"Доступно контейнеров: {selectable_count}")

    def _collect_excluded_idcols(self, elements: Dict[int, Dict],
                                 element_idcol: int) -> set:
        """
        Возвращает set из idCol элемента и всех его потомков.

        v9 FIX (STRICT IDCOL):
        Раньше метод брал current_elem['id'] (ключа нет → KeyError) и искал
        родителя через elements.get(parent_id), хотя elements индексируется
        по idCol. Защита от циклов не работала, диалог падал при открытии.

        Теперь:
        • Старт — по element_idcol (корректный ключ);
        • Поиск потомков — по parent_id (DB-ID) с переводом в idCol через
          _get_id_col_by_db_id на каждом шаге;
        • visited защищает от битых ссылок и циклов.
        """
        excluded = set()
        if element_idcol is None or element_idcol <= 0:
            return excluded

        current_elem = self.collection.get_element_by_id_col(element_idcol)
        if not current_elem:
            return excluded

        excluded.add(element_idcol)

        # BFS по DB-ID родителя → idCol ребёнка
        current_db_id = current_elem.get('db_id')
        if current_db_id is None:
            return excluded

        stack = [current_db_id]
        visited = {current_db_id}

        while stack:
            parent_db_id = stack.pop()
            for _idcol, elem in elements.items():
                if elem.get('parent_id') != parent_db_id:
                    continue
                child_db_id = elem.get('db_id')
                child_idcol = elem.get('id_col')
                if child_idcol and child_idcol not in excluded:
                    excluded.add(child_idcol)
                if child_db_id is not None and child_db_id not in visited:
                    visited.add(child_db_id)
                    stack.append(child_db_id)

        return excluded

    # =====================================================================
    # Обработка выбора
    # =====================================================================
    def _on_selection_changed(self):
        item = self.tree.currentItem()
        if item is None:
            self.btn_ok.setEnabled(False)
            return

        kind = item.data(0, Qt.UserRole + 1)
        self.btn_ok.setEnabled(kind == 'container')

    def _on_double_click(self, item: QTreeWidgetItem, column: int):
        if item is None:
            return
        kind = item.data(0, Qt.UserRole + 1)
        if kind == 'container':
            self._on_accept()

    def _on_accept(self):
        item = self.tree.currentItem()
        if item is None:
            QMessageBox.warning(self, "Ошибка", "Выберите контейнер")
            return

        kind = item.data(0, Qt.UserRole + 1)
        if kind != 'container':
            QMessageBox.warning(self, "Ошибка", "Выбранный элемент не является контейнером")
            return

        self.selected_id_col = item.data(0, Qt.UserRole)
        self.accept()

    # =====================================================================
    # Результат
    # =====================================================================
    def get_selected_id_col(self) -> Optional[int]:
        """Возвращает idCol выбранного контейнера (или None)."""
        return self.selected_id_col