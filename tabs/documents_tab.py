# tabs/documents_tab.py
from PySide6.QtWidgets import (QWidget, QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget,                              QTableWidgetItem, QPushButton, QHBoxLayout, QVBoxLayout,                              QMessageBox, QDialog, QFormLayout, QLineEdit,                              QComboBox, QCheckBox, QLabel, QHeaderView)
from PySide6.QtCore import Qt
from .base_tab import BaseTab
from crud_buttons import CrudButtons
from composition_manager import CompositionManager
from lang.local_translator import LocalTranslator


class DocumentTypeEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_document_type_edit'))
        self.data = data or {}
        self.db = db
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))
        self.chk_dependent = QCheckBox(self.translator.tr('label_dependent'))
        self.chk_dependent.setChecked(self.data.get("lisdependent", False))
        self.chk_hierarchy = QCheckBox(self.translator.tr('label_hierarchical'))
        self.chk_hierarchy.setChecked(self.data.get("lishierarchy", False))
        self.chk_versioned = QCheckBox(self.translator.tr('label_versioned'))
        self.chk_versioned.setChecked(self.data.get("lisversioned", True))

        # Определяем class_id для типа 'DOC'
        doc_class = self.db.execute_query("SELECT id FROM meta.entity_classes WHERE calias = 'DOC'")
        self.class_id = doc_class[0][0] if doc_class else None

        form.addRow(self.translator.tr('field_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.chk_dependent)
        form.addRow(self.chk_hierarchy)
        form.addRow(self.chk_versioned)
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

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "lisdependent": self.chk_dependent.isChecked(),
            "lishierarchy": self.chk_hierarchy.isChecked(),
            "lisversioned": self.chk_versioned.isChecked(),
            "class_id": self.class_id
        }


class CompositionRoleEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_composition_role_edit'))
        self.data = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))
        self.edit_comment = QLineEdit(self.data.get("mcomment", ""))
        form.addRow(self.translator.tr('field_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.translator.tr('field_comment'), self.edit_comment)
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

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "mcomment": self.edit_comment.text()
        }


class CompositionEditDialog(QDialog):
    def __init__(self, parent=None, data=None, doc_types=None, child_types=None, roles=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_composition_edit'))
        self.data = data or {}
        self.db = db
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_parent = QComboBox()
        for tid, tname in doc_types or []:
            self.combo_parent.addItem(f"{tname} ({tid})", tid)
        self.combo_child = QComboBox()
        for tid, tname in child_types or []:
            self.combo_child.addItem(f"{tname} ({tid})", tid)
        self.combo_role = QComboBox()
        for rid, rname in roles or []:
            self.combo_role.addItem(f"{rname} ({rid})", rid)

        self.edit_link_field = QLineEdit(self.data.get("c_link_fieldname", ""))
        self.edit_sort = QLineEdit(str(self.data.get("isortorder", 10)))

        if data:
            idx = self.combo_parent.findData(data.get("parent_entityid"))
            if idx >= 0: self.combo_parent.setCurrentIndex(idx)
            idx = self.combo_child.findData(data.get("child_entityid"))
            if idx >= 0: self.combo_child.setCurrentIndex(idx)
            idx = self.combo_role.findData(data.get("role_id"))
            if idx >= 0: self.combo_role.setCurrentIndex(idx)

        form.addRow(self.translator.tr('field_parent_document'), self.combo_parent)
        form.addRow(self.translator.tr('field_child_entity'), self.combo_child)
        form.addRow(self.translator.tr('field_role'), self.combo_role)
        form.addRow(self.translator.tr('field_link_field'), self.edit_link_field)
        form.addRow(self.translator.tr('field_order'), self.edit_sort)

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

    def get_data(self):
        return {
            "parent_entityid": self.combo_parent.currentData(),
            "child_entityid": self.combo_child.currentData(),
            "role_id": self.combo_role.currentData(),
            "c_link_fieldname": self.edit_link_field.text(),
            "isortorder": int(self.edit_sort.text()) if self.edit_sort.text().isdigit() else 10
        }


class DocumentsTab(BaseTab):
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.translator = LocalTranslator()
        self.composition_manager = CompositionManager(db=self.db, parent_widget=self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.doc_types_tab = self._create_doc_types_tab()
        self.tabs.addTab(self.doc_types_tab, self.translator.tr('tab_document_types'))

        self.roles_tab = self._create_roles_tab()
        self.tabs.addTab(self.roles_tab, self.translator.tr('tab_composition_roles'))

        self.composition_tab = self._create_composition_tab()
        self.tabs.addTab(self.composition_tab, self.translator.tr('tab_master_detail'))

        self.retranslate_ui()

    def retranslate_ui(self):
        self.tabs.setTabText(0, self.translator.tr('tab_document_types'))
        self.tabs.setTabText(1, self.translator.tr('tab_composition_roles'))
        self.tabs.setTabText(2, self.translator.tr('tab_master_detail'))
        if hasattr(self, 'doc_crud'):
            self.doc_crud.retranslate_ui()
            self.role_crud.retranslate_ui()
            self.comp_crud.retranslate_ui()
        self._update_doc_tree_headers()
        self._update_role_table_headers()
        self._update_comp_table_headers()
        self._load_doc_types()
        self._load_roles()
        self._load_compositions()

    def _update_doc_tree_headers(self):
        self.doc_tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('label_dependent'),
            self.translator.tr('label_hierarchical'),
            self.translator.tr('label_versioned')
        ])

    def _update_role_table_headers(self):
        self.role_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_name')
        ])

    def _update_comp_table_headers(self):
        self.comp_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_master'),
            self.translator.tr('field_detail'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field')
        ])

    def _create_doc_types_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.doc_crud = CrudButtons(self)
        layout.addWidget(self.doc_crud)
        self.doc_tree = QTreeWidget()
        self.doc_tree.setHeaderLabels(["ID", self.translator.tr('field_name'), self.translator.tr('field_alias'),
                                       self.translator.tr('label_dependent'), self.translator.tr('label_hierarchical'),
                                       self.translator.tr('label_versioned')])
        self.doc_tree.itemDoubleClicked.connect(self.edit_doc_type)
        layout.addWidget(self.doc_tree)
        self.doc_crud.add_clicked.connect(self.add_doc_type)
        self.doc_crud.edit_clicked.connect(self.edit_doc_type)
        self.doc_crud.delete_clicked.connect(self.delete_doc_type)
        self._load_doc_types()
        return tab

    def _create_roles_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.role_crud = CrudButtons(self)
        layout.addWidget(self.role_crud)
        self.role_table = QTableWidget()
        self.role_table.setColumnCount(3)
        self.role_table.setHorizontalHeaderLabels([self.translator.tr('field_id'),
                                                   self.translator.tr('field_alias'),
                                                   self.translator.tr('field_name')])
        self.role_table.horizontalHeader().setStretchLastSection(True)
        self.role_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.role_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.role_table.itemDoubleClicked.connect(self.edit_role)
        layout.addWidget(self.role_table)
        self.role_crud.add_clicked.connect(self.add_role)
        self.role_crud.edit_clicked.connect(self.edit_role)
        self.role_crud.delete_clicked.connect(self.delete_role)
        self._load_roles()
        return tab

    def _create_composition_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.comp_crud = CrudButtons(self)
        layout.addWidget(self.comp_crud)
        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(5)
        self.comp_table.setHorizontalHeaderLabels([self.translator.tr('field_id'),
                                                   self.translator.tr('field_master'),
                                                   self.translator.tr('field_detail'),
                                                   self.translator.tr('field_role'),
                                                   self.translator.tr('field_link_field')])
        self.comp_table.horizontalHeader().setStretchLastSection(True)
        self.comp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.comp_table.itemDoubleClicked.connect(self.edit_composition)
        layout.addWidget(self.comp_table)
        self.comp_crud.add_clicked.connect(self.add_composition)
        self.comp_crud.edit_clicked.connect(self.edit_composition)
        self.comp_crud.delete_clicked.connect(self.delete_composition)
        self._load_compositions()
        return tab

    def _load_doc_types(self):
        sql = """SELECT id, cname, calias, lisdependent, lishierarchy, lisversioned
                 FROM meta.entitytypes
                 WHERE class_id = (SELECT id FROM meta.entity_classes WHERE calias = 'DOC')
                 ORDER BY cname"""
        rows = self.db.execute_query(sql)
        self.doc_tree.clear()
        for row in rows:
            item = QTreeWidgetItem(self.doc_tree)
            item.setText(0, str(row[0]))
            item.setText(1, row[1])
            item.setText(2, row[2])
            item.setText(3, self.translator.tr('yes') if row[3] else self.translator.tr('no'))
            item.setText(4, self.translator.tr('yes') if row[4] else self.translator.tr('no'))
            item.setText(5, self.translator.tr('yes') if row[5] else self.translator.tr('no'))
            item.setData(0, Qt.UserRole, row[0])

    def add_doc_type(self):
        dlg = DocumentTypeEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO meta.entitytypes
                     (cname, calias, cbaseclass, lisdependent, lishierarchy, lisversioned, class_id)
                     VALUES (%s, %s, 'DOC', %s, %s, %s, %s)"""
            self.db.execute_query(sql, (data["cname"], data["calias"],
                                        data["lisdependent"], data["lishierarchy"],
                                        data["lisversioned"], data["class_id"]), fetch=False)
            self._load_doc_types()

    def edit_doc_type(self):
        item = self.doc_tree.currentItem()
        if not item:
            self.show_warning(self.translator.tr('warning_select_document_type'))
            return
        eid = item.data(0, Qt.UserRole)
        sql = """SELECT cname, calias, lisdependent, lishierarchy, lisversioned
                 FROM meta.entitytypes WHERE id=%s"""
        row = self.db.execute_query(sql, (eid,))
        if not row:
            return
        data = {
            "cname": row[0][0],
            "calias": row[0][1],
            "lisdependent": row[0][2],
            "lishierarchy": row[0][3],
            "lisversioned": row[0][4]
        }
        dlg = DocumentTypeEditDialog(self, data, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """UPDATE meta.entitytypes SET
                        cname=%s, calias=%s, lisdependent=%s, lishierarchy=%s, lisversioned=%s
                     WHERE id=%s"""
            self.db.execute_query(sql, (new_data["cname"], new_data["calias"],
                                        new_data["lisdependent"], new_data["lishierarchy"],
                                        new_data["lisversioned"], eid), fetch=False)
            self._load_doc_types()

    def delete_doc_type(self):
        item = self.doc_tree.currentItem()
        if not item:
            self.show_warning(self.translator.tr('warning_select_document_type'))
            return
        eid = item.data(0, Qt.UserRole)
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_document_type')) == QMessageBox.Yes:
            sql = "DELETE FROM meta.entitytypes WHERE id=%s"
            self.db.execute_query(sql, (eid,), fetch=False)
            self._load_doc_types()

    def _load_roles(self):
        sql = "SELECT id, calias, cname FROM meta.composition_roles ORDER BY id"
        rows = self.db.execute_query(sql)
        self.role_table.setRowCount(0)
        for row in rows:
            pos = self.role_table.rowCount()
            self.role_table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 0:
                    item.setData(Qt.UserRole, val)
                self.role_table.setItem(pos, col, item)

    def add_role(self):
        dlg = CompositionRoleEditDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            sql = "INSERT INTO meta.composition_roles (calias, cname, mcomment) VALUES (%s, %s, %s)"
            self.db.execute_query(sql, (data["calias"], data["cname"], data["mcomment"]), fetch=False)
            self._load_roles()

    def edit_role(self):
        row = self.role_table.currentRow()
        if row < 0:
            self.show_warning(self.translator.tr('warning_select_role'))
            return
        item = self.role_table.item(row, 0)
        rid = item.data(Qt.UserRole)
        sql = "SELECT calias, cname, mcomment FROM meta.composition_roles WHERE id=%s"
        row_data = self.db.execute_query(sql, (rid,))
        if not row_data:
            return
        data = {
            "calias": row_data[0][0],
            "cname": row_data[0][1],
            "mcomment": row_data[0][2]
        }
        dlg = CompositionRoleEditDialog(self, data)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = "UPDATE meta.composition_roles SET calias=%s, cname=%s, mcomment=%s WHERE id=%s"
            self.db.execute_query(sql, (new_data["calias"], new_data["cname"], new_data["mcomment"], rid), fetch=False)
            self._load_roles()

    def delete_role(self):
        row = self.role_table.currentRow()
        if row < 0:
            self.show_warning(self.translator.tr('warning_select_role'))
            return
        item = self.role_table.item(row, 0)
        rid = item.data(Qt.UserRole)
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_role')) == QMessageBox.Yes:
            sql = "DELETE FROM meta.composition_roles WHERE id=%s"
            self.db.execute_query(sql, (rid,), fetch=False)
            self._load_roles()

    def _load_compositions(self):
        sql = """SELECT c.id, p.cname, ch.cname, r.cname, c.c_link_fieldname
                 FROM meta.entity_composition c
                 JOIN meta.entitytypes p ON c.parent_entityid = p.id
                 JOIN meta.entitytypes ch ON c.child_entityid = ch.id
                 JOIN meta.composition_roles r ON c.role_id = r.id
                 ORDER BY c.id"""
        rows = self.db.execute_query(sql)
        self.comp_table.setRowCount(0)
        for row in rows:
            pos = self.comp_table.rowCount()
            self.comp_table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 0:
                    item.setData(Qt.UserRole, row[0])
                self.comp_table.setItem(pos, col, item)

    def get_doc_types_list(self):
        sql = """SELECT id, cname FROM meta.entitytypes
                 WHERE class_id = (SELECT id FROM meta.entity_classes WHERE calias = 'DOC')
                 ORDER BY cname"""
        return self.db.execute_query(sql)

    def get_child_types_list(self):
        sql = "SELECT id, cname FROM meta.entitytypes ORDER BY cname"
        return self.db.execute_query(sql)

    def get_roles_list(self):
        sql = "SELECT id, cname FROM meta.composition_roles ORDER BY cname"
        return self.db.execute_query(sql)

    def add_composition(self):
        doc_types = self.get_doc_types_list()
        child_types = self.get_child_types_list()
        roles = self.get_roles_list()
        dlg = CompositionEditDialog(self, doc_types=doc_types, child_types=child_types, roles=roles, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            success = self.composition_manager.add_composition(
                parent_entityid=data["parent_entityid"],
                child_entityid=data["child_entityid"],
                role_id=data["role_id"],
                link_field=data["c_link_fieldname"],
                sortorder=data["isortorder"]
            )
            if success:
                self._load_compositions()

    def edit_composition(self):
        row = self.comp_table.currentRow()
        if row < 0:
            self.show_warning(self.translator.tr('warning_select_composition'))
            return
        item = self.comp_table.item(row, 0)
        comp_id = item.data(Qt.UserRole)
        sql = """SELECT parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder
                 FROM meta.entity_composition WHERE id=%s"""
        row_data = self.db.execute_query(sql, (comp_id,))
        if not row_data:
            return
        data = {
            "parent_entityid": row_data[0][0],
            "child_entityid": row_data[0][1],
            "role_id": row_data[0][2],
            "c_link_fieldname": row_data[0][3],
            "isortorder": row_data[0][4]
        }
        doc_types = self.get_doc_types_list()
        child_types = self.get_child_types_list()
        roles = self.get_roles_list()
        dlg = CompositionEditDialog(self, data, doc_types, child_types, roles, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            success = self.composition_manager.update_composition(
                comp_id=comp_id,
                parent_entityid=new_data["parent_entityid"],
                child_entityid=new_data["child_entityid"],
                role_id=new_data["role_id"],
                link_field=new_data["c_link_fieldname"],
                sortorder=new_data["isortorder"]
            )
            if success:
                self._load_compositions()

    def delete_composition(self):
        row = self.comp_table.currentRow()
        if row < 0:
            self.show_warning(self.translator.tr('warning_select_composition'))
            return
        item = self.comp_table.item(row, 0)
        comp_id = item.data(Qt.UserRole)
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_composition')) == QMessageBox.Yes:
            self.composition_manager.delete_composition(comp_id)
            self._load_compositions()