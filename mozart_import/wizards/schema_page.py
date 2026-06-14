# mozart_import/wizards/schema_page.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWizardPage, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
from lang.local_translator import LocalTranslator


class SchemaPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = LocalTranslator()
        self.setTitle(self.translator.tr('schema_page_title'))
        self.setSubTitle(self.translator.tr('schema_page_subtitle'))
        layout = QVBoxLayout(self)

        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self.table_selected)
        layout.addWidget(QLabel(self.translator.tr('table_label')))
        layout.addWidget(self.table_combo)

        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        self.fields_table = QTableWidget(0, 2)
        self.fields_table.setHorizontalHeaderLabels(
            [self.translator.tr('field_name_header'), self.translator.tr('field_type_header')])
        self.fields_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fields_table)

        self.loading = QLabel(self.translator.tr('loading_message'))
        layout.addWidget(self.loading)

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('schema_page_title'))
        self.setSubTitle(self.translator.tr('schema_page_subtitle'))
        self.fields_table.setHorizontalHeaderLabels(
            [self.translator.tr('field_name_header'), self.translator.tr('field_type_header')])

    def initializePage(self):
        self.loading.show()
        self.wizard.schema = self.wizard.connector.get_schema()
        self.table_combo.clear()
        for t in self.wizard.schema.tables:
            self.table_combo.addItem(t.name, t.name)
        if self.wizard.schema.tables:
            self.table_selected(0)
        self.loading.hide()

    def table_selected(self, idx):
        table_name = self.table_combo.currentData()
        if not table_name:
            return
        for t in self.wizard.schema.tables:
            if t.name == table_name:
                self.current_table = t
                self.info_label.setText(
                    f"{self.translator.tr('rows_count_label')}: {t.row_count or self.translator.tr('unknown')}, {self.translator.tr('samples_label')}: {len(t.sample_rows or [])}")
                self.fields_table.setRowCount(len(t.fields))
                for i, f in enumerate(t.fields):
                    self.fields_table.setItem(i, 0, QTableWidgetItem(f.name))
                    self.fields_table.setItem(i, 1, QTableWidgetItem(f.field_type.name))
                break

    def validatePage(self):
        self.wizard.selected_table_name = self.table_combo.currentData()
        return True
# -*- coding: utf-8 -*-
