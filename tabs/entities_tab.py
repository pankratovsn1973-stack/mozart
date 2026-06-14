# tabs/entities_tab.py
# -*- coding: utf-8 -*-
# Модуль: Управление сущностями (конфигуратор)
# Версия v9: кнопка "Дублировать", триггер переименования ext-таблиц

from PySide6.QtWidgets import (QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,                              QTreeWidget, QTreeWidgetItem, QMessageBox, QHeaderView,                              QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,                              QPushButton, QTextEdit, QAbstractItemView, QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush
from .base_tab import BaseTab
from crud_buttons import CrudButtons
from widgets import ReferenceEditor
from ide_field_edit import FieldEditDialog
from .entity_subtabs import FieldsTab, BUVISibilityTab, CompositionTab, RoutesTab
from lang.local_translator import LocalTranslator
from composition_manager import CompositionManager


class EntityTypeEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None, read_only_mode=False):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_entity_type_edit'))
        self.data = data or {}
        self.db = db
        self.read_only_mode = read_only_mode
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))
        self.edit_comment = QTextEdit()
        self.edit_comment.setPlainText(self.data.get("mcomment", ""))
        self.edit_comment.setMaximumHeight(100)

        self.ref_class = ReferenceEditor(
            table_name='meta.entity_classes',
            display_field='cname',
            db=self.db
        )
        if self.data.get("class_id"):
            sql = "SELECT cname FROM meta.entity_classes WHERE id = %s"
            res = self.db.execute_query(sql, (self.data["class_id"],))
            if res:
                self.ref_class.set_value(self.data["class_id"], res[0][0])

        self.edit_baseclass = QLineEdit(self.data.get("cbaseclass", ""))
        self.chk_dependent = QCheckBox(self.translator.tr('label_dependent'))
        self.chk_dependent.setChecked(self.data.get("lisdependent", False))
        self.chk_hierarchy = QCheckBox(self.translator.tr('label_hierarchical'))
        self.chk_hierarchy.setChecked(self.data.get("lishierarchy", False))
        self.chk_versioned = QCheckBox(self.translator.tr('label_versioned'))
        self.chk_versioned.setChecked(self.data.get("lisversioned", True))
        self.edit_security = QLineEdit(str(self.data.get("isecuritystrategy", 1)))

        self.combo_status = QComboBox()
        statuses = self.db.execute_query("SELECT id, name FROM meta.object_statuses ORDER BY id")
        for sid, sname in statuses:
            self.combo_status.addItem(sname, sid)
        current_status = self.data.get("status_id")
        if current_status:
            idx = self.combo_status.findData(current_status)
            if idx >= 0:
                self.combo_status.setCurrentIndex(idx)

        form.addRow(self.translator.tr('field_system_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.translator.tr('field_description'), self.edit_comment)
        form.addRow(self.translator.tr('field_entity_class'), self.ref_class)
        form.addRow(self.translator.tr('field_baseclass_legacy'), self.edit_baseclass)
        form.addRow(self.chk_dependent)
        form.addRow(self.chk_hierarchy)
        form.addRow(self.chk_versioned)
        form.addRow(self.translator.tr('field_security_strategy'), self.edit_security)
        form.addRow(self.translator.tr('field_status'), self.combo_status)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        if self.read_only_mode or current_status == 2:
            self.edit_name.setEnabled(False)
            self.edit_alias.setEnabled(False)
            self.ref_class.setReadOnly(True)
            self.edit_baseclass.setEnabled(False)
            self.chk_dependent.setEnabled(False)
            self.chk_hierarchy.setEnabled(False)
            self.chk_versioned.setEnabled(False)
            self.edit_security.setEnabled(False)
            self.edit_comment.setEnabled(False if read_only_mode else True)
            self.combo_status.setEnabled(False if read_only_mode else True)
            if self.read_only_mode:
                btn_ok.setVisible(False)
                btn_cancel.setText(self.translator.tr('btn_close'))

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "mcomment": self.edit_comment.toPlainText(),
            "cbaseclass": self.edit_baseclass.text(),
            "lisdependent": self.chk_dependent.isChecked(),
            "lishierarchy": self.chk_hierarchy.isChecked(),
            "lisversioned": self.chk_versioned.isChecked(),
            "isecuritystrategy": int(self.edit_security.text()) if self.edit_security.text().isdigit() else 1,
            "class_id": self.ref_class.get_value(),
            "status_id": self.combo_status.currentData()
        }


class EntitiesTab(BaseTab):
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.translator = LocalTranslator()
        self.comp_manager = CompositionManager(db=self.db, parent_widget=self)
        splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(splitter)

        left_w = QWidget()
        left_v = QVBoxLayout(left_w)
        self.left_label = QLabel("<b>" + self.translator.tr('entity_types') + "</b>")
        left_v.addWidget(self.left_label)

        # Верхняя панель: кнопки CRUD + Дублировать
        btn_layout = QHBoxLayout()
        self.ent_crud = CrudButtons(self)
        btn_layout.addWidget(self.ent_crud)
        self.btn_duplicate = QPushButton(self.translator.tr('btn_duplicate'))
        self.btn_duplicate.clicked.connect(self.duplicate_entity)
        btn_layout.addWidget(self.btn_duplicate)
        btn_layout.addStretch()
        left_v.addLayout(btn_layout)

        self.tree_entities = QTreeWidget()
        self.tree_entities.setHeaderLabels(
            ["", self.translator.tr('field_system_name'), self.translator.tr('field_alias'),
             self.translator.tr('field_entity_class')])
        self.tree_entities.setColumnWidth(0, 30)
        self.tree_entities.setColumnWidth(1, 180)
        self.tree_entities.setColumnWidth(2, 150)
        self.tree_entities.itemClicked.connect(self.on_entity_selected)
        self.tree_entities.setSelectionMode(QAbstractItemView.ExtendedSelection)
        left_v.addWidget(self.tree_entities)
        splitter.addWidget(left_w)

        right_w = QWidget()
        right_layout = QVBoxLayout(right_w)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        self.fields_tab = FieldsTab(self, db=self.db)
        self.tabs.addTab(self.fields_tab, self.translator.tr('tab_fields'))

        self.bu_tab = BUVISibilityTab(self, db=self.db)
        self.tabs.addTab(self.bu_tab, self.translator.tr('tab_bu_visibility'))

        self.composition_tab = CompositionTab(self, db=self.db)
        self.tabs.addTab(self.composition_tab, self.translator.tr('tab_composition'))

        self.routes_tab = RoutesTab(self, db=self.db)
        self.tabs.addTab(self.routes_tab, self.translator.tr('tab_routes'))

        splitter.addWidget(right_w)
        splitter.setSizes([400, 600])

        self.ent_crud.add_clicked.connect(self.add_entity)
        self.ent_crud.edit_clicked.connect(self.edit_entity)
        self.ent_crud.delete_clicked.connect(self.delete_selected_entities)

        self.current_entity_id = None
        self.current_entity_is_system = False
        self.refresh()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.left_label.setText("<b>" + self.translator.tr('entity_types') + "</b>")
        self.tree_entities.setHeaderLabels(
            ["", self.translator.tr('field_system_name'), self.translator.tr('field_alias'),
             self.translator.tr('field_entity_class')])
        self.tabs.setTabText(0, self.translator.tr('tab_fields'))
        self.tabs.setTabText(1, self.translator.tr('tab_bu_visibility'))
        self.tabs.setTabText(2, self.translator.tr('tab_composition'))
        self.tabs.setTabText(3, self.translator.tr('tab_routes'))
        self.ent_crud.retranslate_ui()
        if hasattr(self, 'btn_duplicate'):
            self.btn_duplicate.setText(self.translator.tr('btn_duplicate'))
        self.fields_tab.retranslate_ui()
        self.bu_tab.retranslate_ui()
        self.composition_tab.retranslate_ui()
        self.routes_tab.retranslate_ui()

    def refresh(self):
        self._load_entities()
        self._update_right_panels(None)

    def _load_entities(self):
        sql = """SELECT et.id, et.cname, et.calias, et.status_id, et.is_system,
                        COALESCE(ec.cname, '') as class_name
                 FROM meta.entitytypes et
                 LEFT JOIN meta.entity_classes ec ON et.class_id = ec.id
                 ORDER BY et.cname"""
        rows = self.db.execute_query(sql)
        self.tree_entities.clear()
        for eid, cname, calias, status_id, is_system, class_name in rows:
            item = QTreeWidgetItem(self.tree_entities)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            if status_id == 2:
                for col in (1, 2, 3):
                    item.setForeground(col, QBrush(Qt.gray))
            if is_system:
                for col in (1, 2, 3):
                    item.setForeground(col, QBrush(Qt.darkCyan))
            item.setText(1, cname)
            item.setText(2, calias)
            item.setText(3, class_name)
            item.setData(0, Qt.UserRole, eid)
            item.setData(0, Qt.UserRole + 1, status_id)
            item.setData(0, Qt.UserRole + 2, is_system)

    def on_entity_selected(self, item):
        self.current_entity_id = item.data(0, Qt.UserRole)
        self.current_entity_is_system = bool(item.data(0, Qt.UserRole + 2))
        self._update_right_panels(self.current_entity_id)

    def _update_right_panels(self, entity_id):
        self.fields_tab.set_entity_id(entity_id, is_system=self.current_entity_is_system)
        self.bu_tab.set_entity_id(entity_id)
        self.composition_tab.set_entity_id(entity_id, is_system=self.current_entity_is_system)

        # Показываем закладку "Маршруты" только для документов
        if entity_id:
            class_alias = self.db.execute_query(
                """SELECT ec.calias FROM meta.entitytypes et
                   JOIN meta.entity_classes ec ON et.class_id = ec.id
                   WHERE et.id = %s""", (entity_id,)
            )
            is_doc = class_alias and class_alias[0][0] == 'DOC'
            self.tabs.setTabVisible(3, is_doc)  # 3 = индекс вкладки Routes
        else:
            self.tabs.setTabVisible(3, False)

        self.routes_tab.set_entity_id(entity_id)

    def _add_fields_by_template(self, entity_id: int, class_id: int):
        sql = """
            SELECT field_name, field_type, calias, nlength, is_indexed,
                   ref_entitytype_id, ref_class_id
            FROM meta.class_field_templates
            WHERE class_id = %s
            ORDER BY sort_order
        """
        rows = self.db.execute_query(sql, (class_id,))
        if not rows:
            return
        for row in rows:
            field_name, field_type, calias, length, indexed, ref_entity_id, ref_class_id = row
            exists = self.db.execute_query(
                "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
                (entity_id, field_name)
            )
            if not exists:
                if field_type == 'R':
                    if ref_entity_id:
                        sql_insert = """
                            INSERT INTO meta.fields
                                (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, ref_entitytypeid, status_id)
                            VALUES (%s, %s, 'R', %s, %s, %s, %s, 1) RETURNING id
                        """
                        res = self.db.execute_query(sql_insert,
                                                    (entity_id, field_name, calias, 0, indexed, ref_entity_id))
                    else:
                        sql_insert = """
                            INSERT INTO meta.fields
                                (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, ref_entitytypeid, status_id)
                            VALUES (%s, %s, 'R', %s, %s, %s, NULL, 1) RETURNING id
                        """
                        res = self.db.execute_query(sql_insert, (entity_id, field_name, calias, 0, indexed))
                else:
                    sql_insert = """
                        INSERT INTO meta.fields
                            (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id)
                        VALUES (%s, %s, %s, %s, %s, %s, 1) RETURNING id
                    """
                    res = self.db.execute_query(sql_insert,
                                                (entity_id, field_name, field_type, calias, length, indexed))
                if res:
                    field_id = res[0][0]
                    try:
                        self.db.execute_procedure("meta.p_field_sync", (field_id,))
                    except Exception as e:
                        self.show_error(f"Ошибка синхронизации поля {field_name}: {e}")

    def _apply_class_composition_templates(self, entity_id: int, class_id: int):
        rows = self.db.execute_query(
            """SELECT child_entitytype_id, role_id, c_link_fieldname, isortorder, is_required
               FROM meta.class_composition_templates
               WHERE class_id = %s
               ORDER BY isortorder""",
            (class_id,)
        )
        if not rows:
            return

        for child_id, role_id, link_field, order, is_required in rows:
            exists = self.db.execute_query(
                """SELECT id FROM meta.entity_composition
                   WHERE parent_entityid = %s 
                     AND child_entityid = %s 
                     AND role_id = %s
                     AND c_link_fieldname = %s""",
                (entity_id, child_id, role_id, link_field)
            )
            if not exists:
                self.comp_manager.add_composition(
                    parent_entityid=entity_id,
                    child_entityid=child_id,
                    role_id=role_id,
                    link_field=link_field,
                    sortorder=order
                )

    def _ensure_doc_files_link(self, entity_id: int, class_id: int):
        class_alias = self.db.execute_query(
            "SELECT calias FROM meta.entity_classes WHERE id = %s", (class_id,)
        )
        if not class_alias or class_alias[0][0] != 'DOC':
            return

        doc_file_id = self.db.execute_query(
            "SELECT entitytype_id FROM meta.system_entity_roles WHERE role_code = 'DOC_FILE' LIMIT 1"
        )
        if not doc_file_id:
            return
        doc_file_id = doc_file_id[0][0]

        role_id = self.db.execute_query(
            "SELECT id FROM meta.composition_roles WHERE calias = 'FILES'"
        )
        if not role_id:
            return
        role_id = role_id[0][0]

        exists = self.db.execute_query(
            """SELECT id FROM meta.entity_composition 
               WHERE parent_entityid = %s 
                 AND child_entityid = %s 
                 AND c_link_fieldname = %s""",
            (entity_id, doc_file_id, 'doc_instance_id')
        )
        if not exists:
            self.db.execute_query(
                """INSERT INTO meta.entity_composition 
                   (parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder)
                   VALUES (%s, %s, %s, %s, %s)""",
                (entity_id, doc_file_id, role_id, 'doc_instance_id', 10),
                fetch=False
            )

    def _apply_system_policies(self, entity_id: int, class_id: int) -> list:
        messages = []
        if class_id is not None:
            class_alias = self.db.execute_query(
                "SELECT calias FROM meta.entity_classes WHERE id = %s", (class_id,)
            )
            if class_alias and class_alias[0][0] == 'DOC':
                doc_file_id = self.db.execute_query(
                    "SELECT entitytype_id FROM meta.system_entity_roles WHERE role_code = 'DOC_FILE' LIMIT 1"
                )
                if doc_file_id:
                    doc_file_id = doc_file_id[0][0]
                    had_link = self.db.execute_query(
                        """SELECT id FROM meta.entity_composition 
                           WHERE parent_entityid = %s 
                             AND child_entityid = %s 
                             AND c_link_fieldname = 'doc_instance_id'""",
                        (entity_id, doc_file_id)
                    )
                    self._ensure_doc_files_link(entity_id, class_id)
                    if not had_link:
                        messages.append("✓ Установлена связь с DOC_FILE")
            self._apply_class_composition_templates(entity_id, class_id)
        return messages

    def duplicate_entity(self):
        """Дублирует выбранную сущность (структуру, не данные)."""
        item = self.tree_entities.currentItem()
        if not item:
            self.show_warning(self.translator.tr('warning_select_entity'))
            return

        eid = item.data(0, Qt.UserRole)

        sql = """SELECT cname, calias, mcomment, cbaseclass, lisdependent, lishierarchy, 
                        lisversioned, isecuritystrategy, class_id, status_id
                 FROM meta.entitytypes WHERE id = %s"""
        row = self.db.execute_query(sql, (eid,))
        if not row:
            return

        old_data = {
            "cname": row[0][0], "calias": row[0][1], "mcomment": row[0][2],
            "cbaseclass": row[0][3], "lisdependent": row[0][4], "lishierarchy": row[0][5],
            "lisversioned": row[0][6], "isecuritystrategy": row[0][7],
            "class_id": row[0][8], "status_id": row[0][9]
        }

        new_cname = old_data["cname"] + "_copy"
        new_calias = old_data["calias"] + "_COPY"

        exists = self.db.execute_query(
            "SELECT id FROM meta.entitytypes WHERE cname = %s OR calias = %s",
            (new_cname, new_calias)
        )
        i = 2
        while exists:
            new_cname = old_data["cname"] + f"_copy{i}"
            new_calias = old_data["calias"] + f"_COPY{i}"
            exists = self.db.execute_query(
                "SELECT id FROM meta.entitytypes WHERE cname = %s OR calias = %s",
                (new_cname, new_calias)
            )
            i += 1

        new_id_row = self.db.execute_query(
            """INSERT INTO meta.entitytypes
               (cname, calias, mcomment, cbaseclass, lisdependent, lishierarchy, 
                lisversioned, isecuritystrategy, class_id, status_id, is_system)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false)
               RETURNING id""",
            (new_cname, new_calias, old_data["mcomment"], old_data["cbaseclass"],
             old_data["lisdependent"], old_data["lishierarchy"],
             old_data["lisversioned"], old_data["isecuritystrategy"],
             old_data["class_id"], 1,)
        )

        if not new_id_row:
            self.show_error(translator.tr("error_copy_failed"))
            return

        new_eid = new_id_row[0][0]

        fields = self.db.execute_query(
            "SELECT cfieldname, cfieldtype, calias, mcomment, nlength, ndecimals, "
            "lisindexed, ref_entitytypeid, isortorder, status_id, is_system "
            "FROM meta.fields WHERE entitytypeid = %s", (eid,)
        )
        for f in fields:
            self.db.execute_query(
                """INSERT INTO meta.fields
                   (entitytypeid, cfieldname, cfieldtype, calias, mcomment, nlength, ndecimals,
                    lisindexed, ref_entitytypeid, isortorder, status_id, is_system)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (new_eid,) + f, fetch=False
            )

        comps = self.db.execute_query(
            "SELECT child_entityid, role_id, c_link_fieldname, isortorder "
            "FROM meta.entity_composition WHERE parent_entityid = %s", (eid,)
        )
        for c in comps:
            exists_comp = self.db.execute_query(
                """SELECT id FROM meta.entity_composition 
                   WHERE parent_entityid = %s AND child_entityid = %s AND c_link_fieldname = %s""",
                (new_eid, c[0], c[2])
            )
            if not exists_comp:
                self.db.execute_query(
                    """INSERT INTO meta.entity_composition
                       (parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (new_eid, c[0], c[1], c[2], c[3]), fetch=False
                )

        child_comps = self.db.execute_query(
            "SELECT parent_entityid, role_id, c_link_fieldname, isortorder "
            "FROM meta.entity_composition WHERE child_entityid = %s", (eid,)
        )
        for c in child_comps:
            exists_comp = self.db.execute_query(
                """SELECT id FROM meta.entity_composition 
                   WHERE parent_entityid = %s AND child_entityid = %s AND c_link_fieldname = %s""",
                (c[0], new_eid, c[2])
            )
            if not exists_comp:
                self.db.execute_query(
                    """INSERT INTO meta.entity_composition
                       (parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (c[0], new_eid, c[1], c[2], c[3]), fetch=False
                )

        for fld in self.db.execute_query("SELECT id FROM meta.fields WHERE entitytypeid = %s", (new_eid,)):
            try:
                self.db.execute_procedure("meta.p_field_sync", (fld[0],))
            except Exception:
                pass

        self._load_entities()
        QMessageBox.information(self, self.translator.tr('info'),
                                f"Сущность скопирована: {new_cname} ({new_calias})")

    def add_entity(self):
        dlg = EntityTypeEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO meta.entitytypes
                     (cname, calias, mcomment, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, class_id, status_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            self.db.execute_query(sql, (data["cname"], data["calias"], data["mcomment"], data["cbaseclass"],
                                        data["lisdependent"], data["lishierarchy"],
                                        data["lisversioned"], data["isecuritystrategy"],
                                        data["class_id"], data["status_id"]), fetch=False)
            self._load_entities()

            if data["class_id"] is not None:
                entity_id = self.db.execute_query(
                    "SELECT id FROM meta.entitytypes WHERE calias = %s", (data["calias"],)
                )
                if entity_id:
                    eid = entity_id[0][0]
                    self._add_fields_by_template(eid, data["class_id"])
                    self._ensure_doc_files_link(eid, data["class_id"])
                    self._apply_class_composition_templates(eid, data["class_id"])
                    if self.current_entity_id == eid:
                        self.fields_tab.load_fields()
                        self._update_right_panels(eid)

    def edit_entity(self):
        item = self.tree_entities.currentItem()
        if not item:
            self.show_warning(self.translator.tr('warning_select_entity'))
            return
        eid = item.data(0, Qt.UserRole)
        status_id = item.data(0, Qt.UserRole + 1)
        is_system = bool(item.data(0, Qt.UserRole + 2))

        sql = """SELECT cname, calias, mcomment, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, class_id, status_id
                 FROM meta.entitytypes WHERE id=%s"""
        row = self.db.execute_query(sql, (eid,))
        if not row:
            return
        old_data = {
            "cname": row[0][0], "calias": row[0][1], "mcomment": row[0][2],
            "cbaseclass": row[0][3], "lisdependent": row[0][4], "lishierarchy": row[0][5],
            "lisversioned": row[0][6], "isecuritystrategy": row[0][7],
            "class_id": row[0][8], "status_id": row[0][9]
        }

        read_only = (status_id == 2)
        dlg = EntityTypeEditDialog(self, old_data, db=self.db, read_only_mode=(is_system or read_only))

        if is_system:
            dlg.exec_()
            messages = self._apply_system_policies(eid, old_data["class_id"])
            if self.current_entity_id == eid:
                self._update_right_panels(eid)
            if messages:
                QMessageBox.information(self, "Системные политики применены", "\n".join(messages))
            return

        if not dlg.exec_():
            return

        new_data = dlg.get_data()
        old_cname = old_data["cname"].strip().lower()
        new_cname = new_data["cname"].strip().lower()

        # Переименование ext-таблицы теперь делает триггер trg_entitytypes_rename
        # Оставляем только проверку на PROD
        if old_cname != new_cname and status_id == 2:
            self.show_error(self.translator.tr('error_rename_prod'))
            return

        sql = """UPDATE meta.entitytypes SET
                    cname=%s, calias=%s, mcomment=%s, cbaseclass=%s, lisdependent=%s,
                    lishierarchy=%s, lisversioned=%s, isecuritystrategy=%s, class_id=%s, status_id=%s
                 WHERE id=%s"""
        self.db.execute_query(sql, (new_data["cname"], new_data["calias"], new_data["mcomment"], new_data["cbaseclass"],
                                    new_data["lisdependent"], new_data["lishierarchy"],
                                    new_data["lisversioned"], new_data["isecuritystrategy"],
                                    new_data["class_id"], new_data["status_id"], eid), fetch=False)

        if new_data["class_id"] is not None:
            self._ensure_doc_files_link(eid, new_data["class_id"])
            self._apply_class_composition_templates(eid, new_data["class_id"])

        self._load_entities()
        if self.current_entity_id == eid:
            self._update_right_panels(eid)

    def delete_selected_entities(self):
        items = self.tree_entities.selectedItems()
        if not items:
            self.show_warning(self.translator.tr('warning_select_entity'))
            return

        dev_ids = []
        prod_names = []
        sys_names = []
        for item in items:
            eid = item.data(0, Qt.UserRole)
            status_id = item.data(0, Qt.UserRole + 1)
            is_system = bool(item.data(0, Qt.UserRole + 2))
            if is_system:
                sys_names.append(item.text(1))
            elif status_id == 1:
                dev_ids.append(eid)
            else:
                prod_names.append(item.text(1))

        if sys_names:
            self.show_error(f"Системные сущности нельзя удалить: {', '.join(sys_names)}")
            return
        if prod_names:
            self.show_error(self.translator.tr('error_prod_entity_delete').format(', '.join(prod_names)))
            return
        if not dev_ids:
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_entities') % len(dev_ids),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for eid in dev_ids:
                self.db.execute_query("DELETE FROM meta.entitytypes WHERE id=%s", (eid,), fetch=False)
            self._load_entities()
            if self.current_entity_id in dev_ids:
                self._update_right_panels(None)
                self.current_entity_id = None