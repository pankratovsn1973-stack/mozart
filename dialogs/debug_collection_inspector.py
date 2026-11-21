# dialogs/debug_collection_inspector.py
# -*- coding: utf-8 -*-
import json
from typing import Optional, Dict, Any, List, Set, Tuple
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QTextEdit, QLabel, QSplitter, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from core.change_log import change_log, ChangeEvent


class DebugCollectionInspector(QDialog):
    """Панель отладки коллекции для ClassEditDialog."""
    save_requested = Signal()

    def __init__(self, parent=None, collection_manager=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Debug Collection Inspector")
        self.resize(1200, 800)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self._collection = collection_manager
        self._log_lines: List[str] = []

        # === Индексы (ключи — id_col) ===
        self._elem_node:       Dict[int, QTreeWidgetItem] = {}
        self._prop_node:       Dict[int, QTreeWidgetItem] = {}
        self._prop_sql_node:   Dict[int, QTreeWidgetItem] = {}
        self._method_node:     Dict[int, QTreeWidgetItem] = {}
        self._method_sql_node: Dict[int, QTreeWidgetItem] = {}
        self._elements_branch: Optional[QTreeWidgetItem] = None
        self._element_props:   Dict[int, Set[int]] = {}
        self._element_methods: Dict[int, Set[int]] = {}

        # === Дебаунс ops ===
        self._pending_ops: Set[Tuple] = set()
        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._flush_pending)

        # === UI ===
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(4, 4, 4, 4)

        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_save = QPushButton("💾 Сохранить (Test)")
        self.btn_clear_log = QPushButton("🗑️ Очистить лог")
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear_log)
        layout.addLayout(btn_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.tree = QTreeWidget()
        # ✅ 9 колонок: добавлен parent_db_id
        self.tree.setHeaderLabels([
            "Объект / Свойство",
            "DB-ID",
            "idCol",
            "parent_db_id",
            "is_inherited",
            "is_deleted",
            "is_changed",
            "version_id",
            "Value / SQL"
        ])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 60)
        self.tree.setColumnWidth(2, 60)
        self.tree.setColumnWidth(3, 90)
        self.tree.setColumnWidth(4, 80)
        self.tree.setColumnWidth(5, 80)
        self.tree.setColumnWidth(6, 80)
        self.tree.setColumnWidth(7, 100)
        self.tree.setColumnWidth(8, 250)
        self.tree.setAlternatingRowColors(True)
        font = QFont("Consolas", 9)
        self.tree.setFont(font)
        splitter.addWidget(self.tree)

        log_frame = QFrame()
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_label = QLabel("📜 Журнал изменений модели (change_log):")
        log_label.setStyleSheet("font-weight: bold; padding: 2px;")
        log_layout.addWidget(log_label)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(font)
        self.log_view.setFixedHeight(180)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_frame)

        splitter.setSizes([600, 180])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.btn_refresh.clicked.connect(self.refresh_tree)
        self.btn_save.clicked.connect(self._on_save_test)
        self.btn_clear_log.clicked.connect(self.clear_log)

        # === Подписка на журнал ===
        change_log.subscribe(self._on_change_event)

        self.add_log(f"[INIT] DebugCollectionInspector создан. "
                     f"collection={'OK' if self._collection else 'None'}")

        if self._collection is not None:
            self.refresh_tree()
    @property
    def collection(self):
        return self._collection

    @collection.setter
    def collection(self, value):
        self._collection = value
        self.add_log(f"[BIND] collection переназначен на {'OK' if value else 'None'}")
        try:
            if self.isVisible():
                self.refresh_tree()
        except RuntimeError:
            pass

    def closeEvent(self, event):
        change_log.unsubscribe(self._on_change_event)
        super().closeEvent(event)

    def add_log(self, line: str):
        if not line:
            return
        self._log_lines.append(line)
        try:
            self.log_view.append(line)
            sb = self.log_view.verticalScrollBar()
            sb.setValue(sb.maximum())
        except RuntimeError:
            pass

    def clear_log(self):
        self._log_lines.clear()
        try:
            self.log_view.clear()
        except RuntimeError:
            pass

    def _on_save_test(self):
        self.save_requested.emit()

    def _on_change_event(self, event: ChangeEvent):
        try:
            self.log_view.append(event.format_line())
            sb = self.log_view.verticalScrollBar()
            sb.setValue(sb.maximum())
        except RuntimeError:
            pass

        if event.kind == 'collection_clear':
            self._pending_ops.clear()
            self._pending_ops.add(('full', 0, 0))
        elif event.kind == 'prop_value':
            if event.id_col is not None:
                self._pending_ops.add(('value', event.id_col, 0))
        elif event.kind in ('prop_meta', 'prop_blob', 'prop_delete'):
            if event.id_col is not None:
                self._pending_ops.add(('prop_meta', event.id_col, 0))
        elif event.kind == 'prop_add':
            self._pending_ops.add(('prop_add', event.element_id, 0))
        elif event.kind in ('method_lang', 'method_delete', 'method_meta'):
            if event.id_col is not None:
                self._pending_ops.add(('method', event.id_col, 0))
        elif event.kind == 'method_add':
            self._pending_ops.add(('method_add', event.element_id, 0))
        elif event.kind == 'element_add':
            self._pending_ops.add(('element_add', event.element_id, 0))
        elif event.kind == 'element_delete':
            self._pending_ops.add(('element_del', event.element_id, 0))
        elif event.kind == 'element_reparent':
            self._pending_ops.add(('reparent', event.element_id, 0))

        self._flush_timer.start(120)

    def _flush_pending(self):
        ops = self._pending_ops
        self._pending_ops = set()

        if any(o[0] == 'full' for o in ops):
            self.refresh_tree()
            return

        for kind in ('value', 'prop_meta', 'prop_add', 'method',
                     'method_add', 'element_add', 'element_del', 'reparent'):
            for op in [o for o in ops if o[0] == kind]:
                _, key, _ = op
                try:
                    if kind == 'value':
                        self._refresh_prop_node_by_idcol(key)
                    elif kind == 'prop_meta':
                        self._refresh_prop_node_by_idcol(key)
                    elif kind == 'prop_add':
                        self._add_prop_node_dynamic(key)
                    elif kind == 'method':
                        self._refresh_method_node_by_idcol(key)
                    elif kind == 'method_add':
                        self._add_method_node_dynamic(key)
                    elif kind == 'element_add':
                        self._add_element_node_dynamic(key)
                    elif kind == 'element_del':
                        self._refresh_element_node(key)
                    elif kind == 'reparent':
                        self._reparent_element_node(key)
                except Exception as e:
                    self.add_log(f"[FLUSH ERROR] {kind} key={key}: {e}")

    def refresh_tree(self):
        self.tree.clear()
        self._elem_node.clear()
        self._prop_node.clear()
        self._prop_sql_node.clear()
        self._method_node.clear()
        self._method_sql_node.clear()
        self._element_props.clear()
        self._element_methods.clear()
        self._elements_branch = None

        if self._collection is None:
            self.add_log("[REFRESH] ❌ collection = None.")
            root = QTreeWidgetItem(self.tree, ["Collection = None", "", "", "", "", "", "", "", ""])
            root.setForeground(0, Qt.GlobalColor.red)
            return

        elements_count = len(self._collection._elements)
        selected_count = len(self._collection._selected_idcols)   # ✅ FIX: _selected_idcols
        deleted_count = len(self._collection._deleted_db_ids)     # ✅ FIX: _deleted_db_ids

        try:
            from ide_core import goProject
            session_date_str = goProject.system_date.toString('yyyy-MM-dd HH:mm:ss')
        except Exception:
            session_date_str = "<unknown>"

        header_text = (
            f"Collection State — elements={elements_count}, "
            f"selected={selected_count}, deleted={deleted_count}, "
            f"session_date={session_date_str}"
        )
        root_item = QTreeWidgetItem(self.tree, [header_text, "", "", "", "", "", "", "", ""])
        root_item.setExpanded(True)

        if elements_count == 0:
            self.add_log(
                f"⚠️ Коллекция пуста. Элементов: 0. "
                f"session_date={session_date_str}."
            )
            empty_node = QTreeWidgetItem(
                root_item,
                ["⚠️ EMPTY COLLECTION — проверьте session_date / dt_start в БД",
                 "", "", "", "", "", "", "", ""]
            )
            empty_node.setForeground(0, Qt.GlobalColor.darkYellow)
            return

        self._elements_branch = QTreeWidgetItem(
            root_item, [f"Elements ({elements_count})", "", "", "", "", "", "", "", ""]
        )
        self._elements_branch.setExpanded(True)

        pending_children = []

        for idcol, elem in sorted(self._collection._elements.items(), key=lambda kv: kv[0]):
            parent_db_id = elem.get('parent_id')
            node = self._create_element_node(self._elements_branch, elem.get('db_id', 0), elem)

            if parent_db_id is not None:
                pending_children.append((parent_db_id, node))

        for parent_db_id, node in pending_children:
            parent_idcol = self._collection._get_id_col_by_db_id(parent_db_id)
            parent_node = self._elem_node.get(parent_idcol) if parent_idcol else None
            if parent_node is not None:
                self._elements_branch.removeChild(node)
                parent_node.addChild(node)

        self.add_log(
            f"[REFRESH] Дерево обновлено (иерархия). Элементов: {elements_count}, "
            f"выделено: {selected_count}, удалено: {deleted_count}"
        )


    def _create_element_node(self, parent: QTreeWidgetItem, eid: int, elem: Dict) -> QTreeWidgetItem:
        """
        Создаёт узел элемента с 9 колонками (включая parent_db_id).
        Наполняет его Properties и Methods.
        НЕ привязывает к родителю — это делает вызывающий код.
        """
        is_inh = "True" if elem.get('isInherited', False) else "False"
        is_del = "True" if elem.get('isDelete', False) else "False"
        is_chg = "True" if elem.get('isDirty', False) else "False"
        ver_id = str(elem.get('chngIDVersion') or elem.get('idVersion') or '')
        elem_id_col = elem.get('id_col', 0)
        parent_db_id = elem.get('parent_id')
        parent_db_id_str = str(parent_db_id) if parent_db_id is not None else '—'

        # ✅ 9 колонок: calias, DB-ID, idCol, parent_db_id, is_inh, is_del, is_chg, version_id, value
        node = QTreeWidgetItem(parent, [
            f"{elem.get('calias', '?')} ({elem.get('cclass', '?')})",
            str(eid),
            str(elem_id_col),
            parent_db_id_str,
            is_inh,
            is_del,
            is_chg,
            ver_id,
            "",
        ])
        node.setExpanded(False)

        # Индексируем по id_col
        self._elem_node[elem_id_col] = node
        self._element_props.setdefault(elem_id_col, set())
        self._element_methods.setdefault(elem_id_col, set())

        # SQL-preview — 9 колонок, значение в колонке 8
        sql_preview = self._generate_element_sql(eid, elem)
        if sql_preview:
            sql_node = QTreeWidgetItem(node, ["", "", "", "", "", "", "", "", sql_preview])
            sql_node.setForeground(8, Qt.GlobalColor.darkGray)

        # Properties
        props_col = self._collection.get_property_collection(elem_id_col)
        if props_col:
            props_branch = QTreeWidgetItem(node, [f"Properties ({len(props_col)})", "", "", "", "", "", "", "", ""])
            for prop in props_col.all_ordered():
                self._add_property_node(props_branch, eid, prop)
        else:
            QTreeWidgetItem(node, ["Properties: None", "", "", "", "", "", "", "", ""])

        # Methods
        methods_col = self._collection.get_method_collection(elem_id_col)
        if methods_col:
            methods_branch = QTreeWidgetItem(node, [f"Methods ({len(methods_col)})", "", "", "", "", "", "", "", ""])
            for method in methods_col.all_ordered():
                self._add_method_node(methods_branch, eid, method)
        else:
            QTreeWidgetItem(node, ["Methods: None", "", "", "", "", "", "", "", ""])

        return node



    def _add_element_node(self, parent: QTreeWidgetItem, eid: int, elem: Dict):
        is_inh = "True" if elem.get('isInherited', False) else "False"
        is_del = "True" if elem.get('isDelete', False) else "False"
        is_chg = "True" if elem.get('isDirty', False) else "False"
        ver_id = str(elem.get('chngIDVersion') or elem.get('idVersion') or '')

        # ✅ FIX: Получаем id_col из элемента
        elem_id_col = elem.get('id_col', 0)

        node = QTreeWidgetItem(parent, [
            f"{elem.get('calias', '?')} ({elem.get('cclass', '?')})",
            str(eid), str(elem_id_col), is_inh, is_del, is_chg, ver_id, ""
        ])
        node.setExpanded(False)

        # ✅ FIX: Используем id_col как ключ
        self._elem_node[elem_id_col] = node
        self._element_props.setdefault(elem_id_col, set())
        self._element_methods.setdefault(elem_id_col, set())

        sql_preview = self._generate_element_sql(eid, elem)
        if sql_preview:
            sql_node = QTreeWidgetItem(node, ["", "", "", "", "", "", "", sql_preview])
            sql_node.setForeground(7, Qt.GlobalColor.darkGray)

        props_col = self._collection.get_property_collection(eid)
        if props_col:
            props_branch = QTreeWidgetItem(node, [f"Properties ({len(props_col)})", "", "", "", "", "", "", ""])
            for prop in props_col.all_ordered():
                self._add_property_node(props_branch, eid, prop)
        else:
            QTreeWidgetItem(node, ["Properties: None", "", "", "", "", "", "", ""])

        methods_col = self._collection.get_method_collection(eid)
        if methods_col:
            methods_branch = QTreeWidgetItem(node, [f"Methods ({len(methods_col)})", "", "", "", "", "", "", ""])
            for method in methods_col.all_ordered():
                self._add_method_node(methods_branch, eid, method)
        else:
            QTreeWidgetItem(node, ["Methods: None", "", "", "", "", "", "", ""])

    def _add_property_node(self, parent: QTreeWidgetItem, eid: int, prop):
        """Отрисовывает свойство; DB-ID, idCol — отдельные колонки. parent_db_id = —."""
        is_inh = getattr(prop, 'isInherited', False)
        is_del = "True" if (getattr(prop, 'isDelete', False) or getattr(prop, 'is_deleted', False)) else "False"
        is_chg = (getattr(prop, 'isDirty', False) or getattr(prop, 'is_changed', False))

        ver_from = "0" if is_inh else str(getattr(prop, 'defined_in_version_id', '') or eid)
        prop_id_col = getattr(prop, 'id_col', 0)

        # ✅ 9 колонок: cname, DB-ID, idCol, parent_db_id, is_inh, is_del, is_chg, version_id, value
        node = QTreeWidgetItem(parent, [
            prop.cname,          # 0
            str(prop.id),        # 1
            str(prop_id_col),    # 2
            "—",                 # 3 parent_db_id (не применим для свойства)
            "True" if is_inh else "False",  # 4
            is_del,              # 5
            "True" if is_chg else "False",  # 6
            ver_from,            # 7
            self._format_prop_value(prop),  # 8
        ])
        self._prop_node[prop_id_col] = node
        if eid in self._element_props:
            self._element_props[eid].add(prop_id_col)

        sql = self._generate_property_sql(prop)
        if sql:
            sql_node = QTreeWidgetItem(node, ["", "", "", "", "", "", "", "", sql])
            sql_node.setForeground(8, Qt.GlobalColor.darkGray)
            self._prop_sql_node[prop_id_col] = sql_node



    def _add_method_node(self, parent: QTreeWidgetItem, eid: int, method):
        """Отрисовывает метод; DB-ID, idCol — отдельные колонки. parent_db_id = —."""
        flags = []
        if getattr(method, 'isDelete', False) or getattr(method, 'is_deleted', False):
            flags.append("DEL")
        if getattr(method, 'isDirty', False) or getattr(method, 'is_changed', False):
            flags.append("DIRTY")
        if getattr(method, 'isInherited', False):
            flags.append("INHERIT")
        if getattr(method, 'is_new', False):
            flags.append("NEW")
        flag_str = ", ".join(flags) if flags else "-"

        chng_id = str(getattr(method, 'chngID', '') or '')
        id_ver = str(getattr(method, 'idVersion', '') or '')
        method_id_col = getattr(method, 'id_col', 0)

        # ✅ 9 колонок
        node = QTreeWidgetItem(parent, [
            method.c_name,                                    # 0
            str(method.id),                                   # 1
            str(method_id_col),                               # 2
            "—",                                              # 3 parent_db_id (не применим)
            "True" if getattr(method, 'isInherited', False) else "False",  # 4
            "True" if (getattr(method, 'isDelete', False) or getattr(method, 'is_deleted', False)) else "False",  # 5
            "True" if (getattr(method, 'isDirty', False) or getattr(method, 'is_changed', False)) else "False",  # 6
            f"{chng_id} / {id_ver}",                          # 7
            f"lang={method.i_lang} {flag_str}",               # 8
        ])
        self._method_node[method_id_col] = node
        if eid in self._element_methods:
            self._element_methods[eid].add(method_id_col)

        sql = self._generate_method_sql(method)
        if sql:
            sql_node = QTreeWidgetItem(node, ["[SQL]", "", "", "", "", "", "", "", sql[:70] + "..."])
            sql_node.setForeground(8, Qt.GlobalColor.darkGray)
            self._method_sql_node[method_id_col] = sql_node


    def _refresh_prop_node_by_idcol(self, prop_id_col: int):
        """Точечно обновляет узел свойства по id_col (9 колонок)."""
        prop = self._collection.get_property_by_id_col(prop_id_col) if self._collection else None
        if prop is None:
            return
        node = self._prop_node.get(prop_id_col)
        if node is None:
            return

        is_inh = getattr(prop, 'isInherited', False)
        is_del = "True" if (getattr(prop, 'isDelete', False) or getattr(prop, 'is_deleted', False)) else "False"
        is_chg = (getattr(prop, 'isDirty', False) or getattr(prop, 'is_changed', False))
        ver_from = "0" if is_inh else str(getattr(prop, 'defined_in_version_id', '') or prop.owner_element_id)

        node.setText(0, prop.cname)
        node.setText(1, str(prop.id))
        node.setText(2, str(prop_id_col))
        # 3: parent_db_id — не меняется (всегда "—")
        node.setText(4, "True" if is_inh else "False")
        node.setText(5, is_del)
        node.setText(6, "True" if is_chg else "False")
        node.setText(7, ver_from)
        node.setText(8, self._format_prop_value(prop))

        font = node.font(0)
        font.setBold(is_chg)
        for col_idx in range(node.columnCount()):
            node.setFont(col_idx, font)

        self._update_prop_sql(prop)



    def _refresh_method_node_by_idcol(self, method_id_col: int):
        """Точечно обновляет узел метода по id_col (9 колонок)."""
        node = self._method_node.get(method_id_col)
        if node is None:
            return
        method = self._collection.get_object_by_id_col(method_id_col) if self._collection else None
        if method is None:
            return

        flags = []
        if getattr(method, 'isDelete', False) or getattr(method, 'is_deleted', False):
            flags.append("DEL")
        if getattr(method, 'isDirty', False) or getattr(method, 'is_changed', False):
            flags.append("DIRTY")
        if getattr(method, 'isInherited', False):
            flags.append("INHERIT")
        if getattr(method, 'is_new', False):
            flags.append("NEW")
        flag_str = ", ".join(flags) if flags else "-"

        chng_id = str(getattr(method, 'chngID', '') or '')
        id_ver = str(getattr(method, 'idVersion', '') or '')

        node.setText(0, method.c_name)
        node.setText(1, str(method.id))
        node.setText(2, str(method_id_col))
        # 3: parent_db_id — не меняется (всегда "—")
        node.setText(4, "True" if getattr(method, 'isInherited', False) else "False")
        node.setText(5, "True" if (getattr(method, 'isDelete', False) or getattr(method, 'is_deleted', False)) else "False")
        node.setText(6, "True" if (getattr(method, 'isDirty', False) or getattr(method, 'is_changed', False)) else "False")
        node.setText(7, f"{chng_id} / {id_ver}")
        node.setText(8, f"lang={method.i_lang} {flag_str}")

        self._update_method_sql(method)


    def _refresh_element_node(self, element_id: int):
        """Обновляет узел элемента по element_id (или id_col) — 9 колонок."""
        # element_id может быть DB-ID или id_col — приводим к id_col
        id_col = element_id
        if self._collection and id_col not in self._collection._elements:
            id_col = self._collection._get_id_col_by_db_id(element_id)

        elem = self._collection.get_element_by_id_col(id_col) if self._collection else None
        if elem is None:
            return

        elem_id_col = elem.get('id_col', 0)
        node = self._elem_node.get(elem_id_col)
        if node is None:
            return

        is_inh = "True" if elem.get('isInherited', False) else "False"
        is_del = "True" if elem.get('isDelete', False) else "False"
        is_chg = "True" if elem.get('isDirty', False) else "False"
        ver_id = str(elem.get('chngIDVersion') or elem.get('idVersion') or '')
        parent_db_id = elem.get('parent_id')
        parent_db_id_str = str(parent_db_id) if parent_db_id is not None else '—'

        node.setText(0, f"{elem.get('calias', '?')} ({elem.get('cclass', '?')})")
        node.setText(1, str(elem.get('db_id', '')))
        node.setText(2, str(elem_id_col))
        node.setText(3, parent_db_id_str)
        node.setText(4, is_inh)
        node.setText(5, is_del)
        node.setText(6, is_chg)
        node.setText(7, ver_id)
        # 8 (Value/SQL) для элемента — пусто

    def _add_prop_node_dynamic(self, element_id: int):
        """
        Добавляет узел нового свойства на лету.
        v7.7: проще перерисовать всю ветку Properties (9 колонок).
        """
        # element_id может быть DB-ID или id_col — приводим к id_col
        id_col = element_id
        if self._collection and id_col not in self._collection._elements:
            id_col = self._collection._get_id_col_by_db_id(element_id)

        elem = self._collection.get_element_by_id_col(id_col) if self._collection else None
        if elem is None:
            return

        elem_id_col = elem.get('id_col', 0)
        elem_node = self._elem_node.get(elem_id_col)
        if elem_node is None:
            self._refresh_element_node(element_id)
            return

        # Ищем ветку Properties
        props_branch = None
        for i in range(elem_node.childCount()):
            c = elem_node.child(i)
            if c.text(0).startswith("Properties"):
                props_branch = c
                break

        if props_branch is None:
            self._refresh_element_node(element_id)
            return

        # Перерисовываем всю ветку
        props_branch.takeChildren()
        col = self._collection.get_property_collection(id_col)
        if col is None:
            props_branch.setText(0, "Properties: None")
            return

        for prop in col.all_ordered():
            self._add_property_node(props_branch, elem.get('db_id', 0), prop)
        props_branch.setText(0, f"Properties ({len(col)})")




    def _add_method_node_dynamic(self, element_id: int):
        """
        Добавляет узел нового метода на лету.
        v7.7: перерисовываем всю ветку Methods (9 колонок).
        """
        # element_id может быть DB-ID или id_col — приводим к id_col
        id_col = element_id
        if self._collection and id_col not in self._collection._elements:
            id_col = self._collection._get_id_col_by_db_id(element_id)

        elem = self._collection.get_element_by_id_col(id_col) if self._collection else None
        if elem is None:
            return

        elem_id_col = elem.get('id_col', 0)
        elem_node = self._elem_node.get(elem_id_col)
        if elem_node is None:
            self._refresh_element_node(element_id)
            return

        # Ищем ветку Methods
        methods_branch = None
        for i in range(elem_node.childCount()):
            c = elem_node.child(i)
            if c.text(0).startswith("Methods"):
                methods_branch = c
                break

        if methods_branch is None:
            self._refresh_element_node(element_id)
            return

        # Перерисовываем всю ветку
        methods_branch.takeChildren()
        col = self._collection.get_method_collection(id_col)
        if col is None:
            methods_branch.setText(0, "Methods: None")
            return

        for m in col.all_ordered():
            self._add_method_node(methods_branch, elem.get('db_id', 0), m)
        methods_branch.setText(0, f"Methods ({len(col)})")


    def _add_element_node_dynamic(self, element_id: int):
        """
        Добавляет узел нового элемента на лету.
        v7.7: 9 колонок, прикрепление к родителю по parent_db_id.
        """
        if self._elements_branch is None:
            return

        # element_id может быть DB-ID или id_col — приводим к id_col
        id_col = element_id
        if self._collection and id_col not in self._collection._elements:
            id_col = self._collection._get_id_col_by_db_id(element_id)

        elem = self._collection.get_element_by_id_col(id_col) if self._collection else None
        if elem is None:
            return

        elem_id_col = elem.get('id_col', 0)
        if elem_id_col in self._elem_node:
            self._refresh_element_node(element_id)
            return

        # Создаём узел через общий метод
        node = self._create_element_node(self._elements_branch, elem.get('db_id', 0), elem)

        # Прикрепляем к родителю (если есть)
        parent_db_id = elem.get('parent_id')
        if parent_db_id is not None:
            parent_idcol = self._collection._get_id_col_by_db_id(parent_db_id)
            parent_node = self._elem_node.get(parent_idcol) if parent_idcol else None
            if parent_node is not None:
                self._elements_branch.removeChild(node)
                parent_node.addChild(node)

        self._elements_branch.setText(
            0, f"Elements ({len(self._collection._elements)})"
        )


    def _rebuild_elements_branch(self):
        """
        Полная перестройка ветки Elements (после reparent).
        v7.7: строим иерархию по parent_db_id, 9 колонок.
        """
        if self._elements_branch is None:
            return

        expanded = self._elements_branch.isExpanded()

        # Очищаем ветку и все индексы
        self._elements_branch.takeChildren()
        self._elem_node.clear()
        self._prop_node.clear()
        self._prop_sql_node.clear()
        self._method_node.clear()
        self._method_sql_node.clear()
        self._element_props.clear()
        self._element_methods.clear()

        # Сначала все узлы в _elements_branch
        pending_children = []  # (parent_db_id, node)

        for idcol, elem in sorted(self._collection._elements.items(), key=lambda kv: kv[0]):
            parent_db_id = elem.get('parent_id')
            node = self._create_element_node(self._elements_branch, elem.get('db_id', 0), elem)

            if parent_db_id is not None:
                pending_children.append((parent_db_id, node))

        # Прикрепляем детей к родителям
        for parent_db_id, node in pending_children:
            parent_idcol = self._collection._get_id_col_by_db_id(parent_db_id)
            parent_node = self._elem_node.get(parent_idcol) if parent_idcol else None
            if parent_node is not None:
                self._elements_branch.removeChild(node)
                parent_node.addChild(node)
            # Если родителя нет — остаётся на верхнем уровне (битые ссылки)

        self._elements_branch.setText(
            0, f"Elements ({len(self._collection._elements)})"
        )
        self._elements_branch.setExpanded(expanded)


    def _reparent_element_node(self, element_id: int):
        """После reparent перестраиваем всё дерево Elements (структура изменилась)."""
        self._rebuild_elements_branch()

    def _find_prop_by_id_col(self, prop_id_col: int):
        """Возвращает ObjectProperty по id_col (делегирует в CollectionManager)."""
        if self._collection is None:
            return None
        return self._collection.get_property_by_id_col(prop_id_col)

    def _find_method_by_id_col(self, method_id_col: int):
        """Возвращает MethodItem по id_col (делегирует в CollectionManager)."""
        if self._collection is None:
            return None
        obj = self._collection.get_object_by_id_col(method_id_col)
        if obj is None:
            return None
        from core.method_item import MethodItem
        return obj if isinstance(obj, MethodItem) else None


    def _format_prop_value(self, prop) -> str:
        if getattr(prop, 'is_blob', False):
            size = len(prop.blob_value) if prop.blob_value else 0
            return f"[BLOB:{prop.blob_name or '?'}, {size}B]"
        v = str(prop.value) if prop.value else "(empty)"
        return v[:200]

    def _update_prop_sql(self, prop):
        """
        Обновляет (или создаёт/удаляет) SQL-узел свойства.
        v7.7: 9 колонок, SQL в колонке 8.
        """
        sql_text = self._generate_property_sql(prop)
        prop_id_col = getattr(prop, 'id_col', 0)
        sql_node = self._prop_sql_node.get(prop_id_col)

        if sql_node is None and sql_text:
            parent = self._prop_node.get(prop_id_col)
            if parent is None:
                return
            sql_node = QTreeWidgetItem(parent, ["[SQL]", "", "", "", "", "", "", "", ""])
            sql_node.setForeground(8, Qt.GlobalColor.darkGray)
            self._prop_sql_node[prop_id_col] = sql_node

        if sql_node is not None:
            if sql_text:
                sql_node.setText(8, sql_text[:70] + "..."
                                 if len(sql_text) > 70 else sql_text)
            else:
                parent = sql_node.parent()
                if parent is not None:
                    parent.removeChild(sql_node)
                self._prop_sql_node.pop(prop_id_col, None)


    def _update_method_sql(self, method):
        """
        Обновляет (или создаёт/удаляет) SQL-узел метода.
        v7.7: 9 колонок, SQL в колонке 8.
        """
        sql_text = self._generate_method_sql(method)
        method_id_col = getattr(method, 'id_col', 0)
        sql_node = self._method_sql_node.get(method_id_col)

        if sql_node is None and sql_text:
            parent = self._method_node.get(method_id_col)
            if parent is None:
                return
            sql_node = QTreeWidgetItem(parent, ["[SQL]", "", "", "", "", "", "", "", ""])
            sql_node.setForeground(8, Qt.GlobalColor.darkGray)
            self._method_sql_node[method_id_col] = sql_node

        if sql_node is not None:
            if sql_text:
                sql_node.setText(8, sql_text[:70] + "..."
                                 if len(sql_text) > 70 else sql_text)
            else:
                parent = sql_node.parent()
                if parent is not None:
                    parent.removeChild(sql_node)
                self._method_sql_node.pop(method_id_col, None)


    def _generate_element_sql(self, eid: int, elem: Dict) -> str:
        """SQL-preview для элемента (текст, без привязки к колонкам)."""
        if elem.get('isDelete', False):
            vid = elem.get('idVersion') or elem.get('chngIDVersion')
            if vid:
                return f"UPDATE class_version SET dt_end = now() WHERE id = {vid};"
            return "-- DELETE (no version id)"

        if elem.get('is_new', False) and not elem.get('chngID'):
            return f"-- INSERT mozartclasses + class_version (new element {eid})"

        vid = elem.get('chngIDVersion') or elem.get('idVersion')
        if vid:
            geo = json.dumps({'x': elem.get('x', 0), 'y': elem.get('y', 0)})
            return f"UPDATE class_version SET txt_properties = '{geo}' WHERE id = {vid};"
        return f"-- NO SQL (element {eid} has no version)"

    def _generate_property_sql(self, prop) -> str:
        """SQL-preview для свойства (текст, без привязки к колонкам)."""
        if getattr(prop, 'isDelete', False):
            pid = getattr(prop, 'chngID', None) or prop.id
            if pid and pid > 0:
                return f"UPDATE class_version_properties SET dt_end = now() WHERE id = {pid};"
            return "-- DELETE (new prop, skip)"

        is_dirty = (getattr(prop, 'isDirty', False) or getattr(prop, 'is_changed', False))
        if is_dirty:
            pid = getattr(prop, 'chngID', None) or prop.id
            if pid and pid > 0:
                val = (prop.value or "").replace("'", "''")
                return f"UPDATE class_version_properties SET c_value = '{val}' WHERE id = {pid};"
            return f"-- INSERT class_version_properties (new prop {prop.cname})"

        return ""

    def _generate_method_sql(self, method) -> str:
        """SQL-preview для метода (текст, без привязки к колонкам)."""
        if getattr(method, 'isDelete', False) or getattr(method, 'is_deleted', False):
            mid = getattr(method, 'chngID', None) or method.id
            if mid and mid > 0:
                return f"UPDATE method_class_relation SET dt_end = now() WHERE id_method = {mid};"
            return "-- DELETE (new method, skip)"
        if getattr(method, 'is_new', False):
            return f"-- INSERT method + method_version + method_class_relation ({method.c_name})"
        if getattr(method, 'isDirty', False) or getattr(method, 'is_changed', False):
            mid = getattr(method, 'chngID', None) or method.id
            if mid and mid > 0:
                return f"UPDATE method_version SET i_lang = {method.i_lang} WHERE id_method = {mid} AND dt_end IS NULL;"
            return f"-- NO SQL (method {method.c_name} has no id)"
        return ""