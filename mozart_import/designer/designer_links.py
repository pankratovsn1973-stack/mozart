# mozart_import/designer/designer_links.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QVBoxLayout, QDialogButtonBox, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt


class ImportLinksManager:
    """Управление связями импорта (таблица links_table)."""
    def __init__(self, parent, links_table, translator, source_tables, mozart_entities):
        self.parent = parent
        self.links_table = links_table
        self.translator = translator
        self.source_tables = source_tables
        self.mozart_entities = mozart_entities
        self.import_links = []

    def set_source_tables(self, tables):
        self.source_tables = tables

    def set_mozart_entities(self, entities):
        self.mozart_entities = entities

    def add_import_link(self):
        dlg = QDialog(self.parent)
        dlg.setWindowTitle(self.translator.tr('add_import_link_title'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        src_table_combo = QComboBox()
        for t in self.source_tables:
            src_table_combo.addItem(t.name, t.name)
        form.addRow(self.translator.tr('source_table'), src_table_combo)
        src_field_combo = QComboBox()
        src_table_combo.currentIndexChanged.connect(lambda: self.update_src_fields(src_table_combo, src_field_combo))
        self.update_src_fields(src_table_combo, src_field_combo)
        form.addRow(self.translator.tr('source_field'), src_field_combo)
        target_entity_combo = QComboBox()
        for ent in self.mozart_entities:
            target_entity_combo.addItem(f"{ent['cname']} ({ent['calias']})", ent['id'])
        form.addRow(self.translator.tr('target_entity'), target_entity_combo)
        target_field_combo = QComboBox()
        target_entity_combo.currentIndexChanged.connect(lambda: self.update_target_fields(target_entity_combo, target_field_combo))
        self.update_target_fields(target_entity_combo, target_field_combo)
        form.addRow(self.translator.tr('target_field'), target_field_combo)
        type_combo = QComboBox()
        type_combo.addItem(self.translator.tr('import_type'), 'import')
        type_combo.addItem(self.translator.tr('sourceid_type'), 'sourceid')
        form.addRow(self.translator.tr('type'), type_combo)
        layout.addLayout(form)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_():
            target_field = target_field_combo.currentData()
            self.import_links.append({
                'source_table': src_table_combo.currentData(),
                'source_field': src_field_combo.currentData(),
                'target_entity_id': target_entity_combo.currentData(),
                'target_field': target_field,
                'type': type_combo.currentData()
            })
            self.update_import_links_table()

    def update_src_fields(self, src_table_combo, src_field_combo):
        table_name = src_table_combo.currentData()
        src_field_combo.clear()
        for t in self.source_tables:
            if t.name == table_name:
                for f in t.fields:
                    src_field_combo.addItem(f.name, f.name)
                break

    def update_target_fields(self, target_entity_combo, target_field_combo):
        entity_id = target_entity_combo.currentData()
        target_field_combo.clear()
        for ent in self.mozart_entities:
            if ent['id'] == entity_id:
                for fname in ent['fields']:
                    target_field_combo.addItem(fname, fname)
                break

    def update_import_links_table(self):
        self.links_table.setRowCount(len(self.import_links))
        for row, link in enumerate(self.import_links):
            self.links_table.setItem(row, 0, QTableWidgetItem(link['source_table']))
            self.links_table.setItem(row, 1, QTableWidgetItem(link['source_field']))
            entity_name = ''
            for ent in self.mozart_entities:
                if ent['id'] == link['target_entity_id']:
                    entity_name = ent['cname']
                    break
            self.links_table.setItem(row, 2, QTableWidgetItem(entity_name))
            self.links_table.setItem(row, 3, QTableWidgetItem(link['target_field'] or ''))
            self.links_table.setItem(row, 4, QTableWidgetItem(link['type']))
            btn = QPushButton(self.translator.tr('delete'))
            btn.clicked.connect(lambda checked, r=row: self.remove_import_link(r))
            self.links_table.setCellWidget(row, 5, btn)

    def remove_import_link(self, row):
        self.import_links.pop(row)
        self.update_import_links_table()