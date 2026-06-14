# mozart_import/designer/designer_trees.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QTreeWidgetItem, QMenu, QMessageBox, QDialog, QFormLayout, QComboBox, QVBoxLayout, QDialogButtonBox, QLineEdit, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from .designer_utils import to_field_name


class SourceTreeManager:
    """Управление деревом таблиц источника."""
    def __init__(self, parent, source_tree, source_links_table, translator, connector):
        self.parent = parent
        self.source_tree = source_tree
        self.source_links_table = source_links_table
        self.translator = translator
        self.connector = connector
        self.source_tables = []
        self.source_fk_links = []

    def load_source(self):
        self.source_tree.clear()
        schema = self.connector.get_schema()
        self.source_tables = schema.tables
        for table in self.source_tables:
            row_count = self.connector.get_row_count(table.name)
            count_str = str(row_count) if row_count is not None else '?'
            item = QTreeWidgetItem([table.name, count_str])
            item.setData(0, Qt.UserRole, table.name)
            for field in table.fields:
                field_item = QTreeWidgetItem([f"  {field.name} ({field.field_type.name})", ""])
                field_item.setData(0, Qt.UserRole, field.name)
                field_item.setFlags(field_item.flags() | Qt.ItemIsUserCheckable)
                field_item.setCheckState(0, Qt.Unchecked)
                item.addChild(field_item)
            self.source_tree.addTopLevelItem(item)
        self.detect_source_fk_links()
        self.update_source_links_table()

    def detect_source_fk_links(self):
        self.source_fk_links = []
        for table in self.source_tables:
            for field in table.fields:
                if field.is_foreign_key and field.refers_to:
                    self.source_fk_links.append({
                        'source_table': table.name,
                        'source_field': field.name,
                        'target_table': field.refers_to,
                        'target_field': 'id'
                    })

    def update_source_links_table(self):
        self.source_links_table.setRowCount(len(self.source_fk_links))
        for row, link in enumerate(self.source_fk_links):
            self.source_links_table.setItem(row, 0, QTableWidgetItem(link['source_table']))
            self.source_links_table.setItem(row, 1, QTableWidgetItem(link['source_field']))
            self.source_links_table.setItem(row, 2, QTableWidgetItem(link['target_table']))
            self.source_links_table.setItem(row, 3, QTableWidgetItem(link['target_field']))

    def get_checked_fields(self):
        checked = []
        root = self.source_tree.invisibleRootItem()
        for i in range(root.childCount()):
            table_item = root.child(i)
            for j in range(table_item.childCount()):
                field_item = table_item.child(j)
                if field_item.checkState(0) == Qt.Checked:
                    checked.append({
                        'source_field_name': field_item.data(0, Qt.UserRole),
                        'source_table': table_item.data(0, Qt.UserRole)
                    })
        return checked

    def set_checks_for_table(self, table_item, state):
        for i in range(table_item.childCount()):
            field_item = table_item.child(i)
            field_item.setCheckState(0, state)

    def add_source_link(self, table_item):
        table_name = table_item.data(0, Qt.UserRole)
        dlg = QDialog(self.parent)
        dlg.setWindowTitle(self.translator.tr('add_source_link_title'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        source_field_combo = QComboBox()
        for t in self.source_tables:
            if t.name == table_name:
                for f in t.fields:
                    source_field_combo.addItem(f.name, f.name)
                break
        form.addRow(self.translator.tr('source_field'), source_field_combo)
        target_table_combo = QComboBox()
        for t in self.source_tables:
            if t.name != table_name:
                target_table_combo.addItem(t.name, t.name)
        form.addRow(self.translator.tr('target_table'), target_table_combo)
        target_field_combo = QComboBox()
        target_table_combo.currentIndexChanged.connect(lambda: self.update_target_fields(target_table_combo, target_field_combo))
        self.update_target_fields(target_table_combo, target_field_combo)
        form.addRow(self.translator.tr('target_field'), target_field_combo)
        layout.addLayout(form)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_():
            self.source_fk_links.append({
                'source_table': table_name,
                'source_field': source_field_combo.currentData(),
                'target_table': target_table_combo.currentData(),
                'target_field': target_field_combo.currentData()
            })
            self.update_source_links_table()

    def update_target_fields(self, target_table_combo, target_field_combo):
        target_table = target_table_combo.currentData()
        target_field_combo.clear()
        for t in self.source_tables:
            if t.name == target_table:
                for f in t.fields:
                    target_field_combo.addItem(f.name, f.name)
                break

    def preview_table(self, table_item):
        table_name = table_item.data(0, Qt.UserRole)
        sample = self.connector.get_table_sample(table_name, limit=20)
        if not sample:
            QMessageBox.information(self.parent, self.translator.tr('info'), self.translator.tr('no_data'))
            return
        dlg = QDialog(self.parent)
        dlg.setWindowTitle(self.translator.tr('preview_table_title').format(table_name))
        layout = QVBoxLayout(dlg)
        table = QTableWidget()
        headers = list(sample[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(sample))
        for i, row in enumerate(sample):
            for j, col in enumerate(headers):
                table.setItem(i, j, QTableWidgetItem(str(row.get(col, ''))))
        layout.addWidget(table)
        dlg.exec_()


class MozartTreeManager:
    def __init__(self, parent, mozart_tree, translator, db):
        self.parent = parent
        self.mozart_tree = mozart_tree
        self.translator = translator
        self.db = db
        self.mozart_entities = []

    def load_mozart(self):
        self.mozart_tree.clear()
        rows = self.db.execute_query("SELECT id, cname, calias, class_id FROM meta.entitytypes ORDER BY cname")
        self.mozart_entities = []
        for eid, cname, calias, class_id in rows:
            class_res = self.db.execute_query("SELECT calias FROM meta.entity_classes WHERE id=%s", (class_id,))
            class_alias = class_res[0][0] if class_res else "DICT"
            fields = self.db.execute_query("SELECT cfieldname, cfieldtype FROM meta.fields WHERE entitytypeid=%s", (eid,))
            item = QTreeWidgetItem([f"{cname} ({calias} - {class_alias})", ""])
            item.setData(0, Qt.UserRole, eid)
            for fname, ftype in fields:
                fitem = QTreeWidgetItem([f"  {fname} ({ftype})", ""])
                fitem.setData(0, Qt.UserRole, fname)
                item.addChild(fitem)
            self.mozart_tree.addTopLevelItem(item)
            self.mozart_entities.append({
                'id': eid, 'cname': cname, 'calias': calias, 'class_alias': class_alias, 'fields': [f[0] for f in fields]
            })
        return self.mozart_entities

    def get_entity_by_id(self, entity_id):
        for ent in self.mozart_entities:
            if ent['id'] == entity_id:
                return ent
        return None