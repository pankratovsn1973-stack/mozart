# mozart_import/wizards/mapping_detail_page.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWizardPage, QVBoxLayout, QHBoxLayout, QTableWidget,                              QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,                              QComboBox, QCheckBox, QSpinBox)
from PySide6.QtCore import Qt
from lang.local_translator import LocalTranslator
from ..utils.field_creator import FieldCreator


class MappingDetailPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = LocalTranslator()
        self.setTitle(self.translator.tr('detail_page_title'))
        self.setSubTitle(self.translator.tr('detail_page_subtitle'))

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_entity'),
            self.translator.tr('target_field'),
            self.translator.tr('mozart_type'),
            self.translator.tr('length'),
            self.translator.tr('source_id'),
            self.translator.tr('action')
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton(self.translator.tr('apply_mapping_btn'))
        self.btn_apply.clicked.connect(self.apply_mapping)
        self.btn_back = QPushButton(self.translator.tr('back_btn'))
        self.btn_back.clicked.connect(lambda: self.wizard.back())
        btn_layout.addWidget(self.btn_back)
        btn_layout.addWidget(self.btn_apply)
        layout.addLayout(btn_layout)

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('detail_page_title'))
        self.setSubTitle(self.translator.tr('detail_page_subtitle'))
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_entity'),
            self.translator.tr('target_field'),
            self.translator.tr('mozart_type'),
            self.translator.tr('length'),
            self.translator.tr('source_id'),
            self.translator.tr('action')
        ])
        self.btn_apply.setText(self.translator.tr('apply_mapping_btn'))
        self.btn_back.setText(self.translator.tr('back_btn'))

    def initializePage(self):
        self.load_mappings()

    def load_mappings(self):
        links = getattr(self.wizard, 'links', [])
        source_nodes = {node.id: node for node in getattr(self.wizard, 'source_nodes', [])}
        target_nodes = {}
        if hasattr(self.wizard, 'pending_entities'):
            for node_item, _ in self.wizard.pending_entities:
                target_nodes[node_item.node.id] = node_item.node

        self.table.setRowCount(len(links))
        for row, link in enumerate(links):
            source_node = source_nodes.get(link['source_node_id'])
            target_node = target_nodes.get(link['target_node_id'])
            self.table.setItem(row, 0, QTableWidgetItem(source_node.name if source_node else ''))
            self.table.setItem(row, 1, QTableWidgetItem(link['source_field']))
            self.table.setItem(row, 2, QTableWidgetItem(target_node.name if target_node else ''))

            combo_target = QComboBox()
            combo_target.addItem("-- " + self.translator.tr('ignore_field') + " --", "")
            if target_node and target_node.entity_id:
                fields = self.wizard.db.execute_query(
                    "SELECT cfieldname, calias FROM meta.fields WHERE entitytypeid=%s",
                    (target_node.entity_id,)
                )
                for fname, calias in fields:
                    combo_target.addItem(f"{calias} ({fname})", fname)
            combo_target.addItem("++ " + self.translator.tr('create_new_field') + " ++", "__NEW__")
            if link.get('target_field'):
                idx = combo_target.findData(link['target_field'])
                if idx >= 0:
                    combo_target.setCurrentIndex(idx)
            combo_target.currentIndexChanged.connect(lambda idx, r=row, cb=combo_target: self.on_target_field_changed(r, cb))
            self.table.setCellWidget(row, 3, combo_target)

            type_combo = QComboBox()
            type_combo.addItems(["C", "N", "I", "D", "T", "L", "M", "R"])
            type_combo.setEnabled(False)
            if link.get('target_field') and not self.field_exists(target_node, link['target_field']):
                type_combo.setEnabled(True)
                type_combo.setCurrentText(link.get('field_type', 'C'))
            self.table.setCellWidget(row, 4, type_combo)

            length_spin = QSpinBox()
            length_spin.setRange(1, 10000)
            length_spin.setValue(link.get('field_length', 255))
            length_spin.setEnabled(False)
            if link.get('target_field') and not self.field_exists(target_node, link['target_field']):
                length_spin.setEnabled(True)
            self.table.setCellWidget(row, 5, length_spin)

            chk = QCheckBox()
            chk.setChecked(link.get('is_source_id', False))
            chk.stateChanged.connect(lambda state, r=row: self.on_source_id_changed(r, state))
            self.table.setCellWidget(row, 6, chk)

            btn = QPushButton(self.translator.tr('delete_btn'))
            btn.clicked.connect(lambda checked, r=row: self.remove_link(r))
            self.table.setCellWidget(row, 7, btn)

    def field_exists(self, target_node, field_name):
        if not target_node or not target_node.entity_id:
            return False
        res = self.wizard.db.execute_query(
            "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
            (target_node.entity_id, field_name)
        )
        return bool(res)

    def on_target_field_changed(self, row, combo):
        if combo.currentData() == "__NEW__":
            self.create_new_field(row)

    def create_new_field(self, row):
        source_field = self.table.item(row, 1).text()
        from .wizard_dialogs import NewFieldDialog
        dlg = NewFieldDialog(self, self.wizard.db)
        # Предлагаем имя на основе исходного поля
        import re
        suggested = re.sub(r'[^a-zA-Z0-9_]', '_', source_field)
        if suggested[0].isdigit():
            suggested = '_' + suggested
        dlg.name_edit.setText(suggested)
        if dlg.exec_():
            data = dlg.get_data()
            links = getattr(self.wizard, 'links', [])
            if row < len(links):
                links[row]['target_field'] = data['cfieldname']
                links[row]['field_type'] = data['cfieldtype']
                links[row]['field_length'] = data['nlength']
            self.load_mappings()

    def on_source_id_changed(self, row, state):
        for r in range(self.table.rowCount()):
            if r != row:
                chk = self.table.cellWidget(r, 6)
                if chk:
                    chk.blockSignals(True)
                    chk.setChecked(False)
                    chk.blockSignals(False)
        links = getattr(self.wizard, 'links', [])
        if row < len(links):
            links[row]['is_source_id'] = (state == Qt.Checked)

    def remove_link(self, row):
        if hasattr(self.wizard, 'links'):
            self.wizard.links.pop(row)
        self.load_mappings()

    def apply_mapping(self):
        has_source_id = any(self.table.cellWidget(r, 6).isChecked() for r in range(self.table.rowCount()))
        if not has_source_id:
            reply = QMessageBox.question(self, self.translator.tr('warning'),
                                         self.translator.tr('no_source_id_warning'),
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        links = getattr(self.wizard, 'links', [])
        for row in range(self.table.rowCount()):
            if row >= len(links):
                break
            combo = self.table.cellWidget(row, 3)
            target_field = combo.currentData() if combo else None
            if target_field and target_field != "__NEW__":
                links[row]['target_field'] = target_field
                links[row]['field_type'] = self.table.cellWidget(row, 4).currentText()
                links[row]['field_length'] = self.table.cellWidget(row, 5).value()
        self.wizard.import_links = links
        self.wizard.next()