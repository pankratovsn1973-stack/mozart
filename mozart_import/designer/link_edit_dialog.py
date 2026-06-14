# mozart_import/designer/link_edit_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,                              QComboBox, QCheckBox, QDialogButtonBox, QHeaderView,                              QMessageBox)
from PySide6.QtCore import Qt
from lang.local_translator import LocalTranslator


class LinkEditDialog(QDialog):
    """
    Диалог настройки связи импорта.
    source_fields – список имён полей источника, уже отфильтрованных пользователем (чекбоксы).
    target_fields – полный список полей Mozart (включая sourceid).
    source_refs – словарь ссылок {field_name: {'is_ref': bool, 'ref_table': str, 'ref_field': str}}
    """
    def __init__(self, source_fields: list, target_fields: list, current_mappings=None, source_refs=None, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('mapping_details_title'))
        self.resize(800, 400)

        self.source_fields = source_fields
        self.target_fields = target_fields
        self.current_mappings = current_mappings or []
        self.source_refs = source_refs or {}
        self.mappings = []

        layout = QVBoxLayout(self)

        self.table = QTableWidget(len(source_fields), 4)
        self.table.setHorizontalHeaderLabels([
            self.translator.tr('source_field'),
            self.translator.tr('target_field'),
            self.translator.tr('sourceid_type'),
            "Ссылка"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        for row, src_field in enumerate(source_fields):
            # Поле источника (только чтение)
            item = QTableWidgetItem(src_field)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, item)

            # Выпадающий список полей Mozart
            combo = QComboBox()
            combo.addItem(self.translator.tr('ignore_field'), None)  # ключ None = игнорировать
            for tgt in target_fields:
                combo.addItem(tgt, tgt)
            self.table.setCellWidget(row, 1, combo)

            # Чекбокс ключевого поля (sourceid)
            chk_key = QCheckBox()
            chk_key.stateChanged.connect(lambda state, r=row: self._on_source_id_changed(r, state))
            self.table.setCellWidget(row, 2, chk_key)

            # Чекбокс "ссылка" (информативный)
            chk_ref = QCheckBox()
            ref_info = self.source_refs.get(src_field, {})
            if ref_info.get('is_ref'):
                chk_ref.setChecked(True)
                chk_ref.setText(f"→ {ref_info.get('ref_table','')}.{ref_info.get('ref_field','')}")
                chk_ref.setEnabled(True)
            else:
                chk_ref.setChecked(False)
                chk_ref.setEnabled(False)
                chk_ref.setText("")
            self.table.setCellWidget(row, 3, chk_ref)

        # Восстанавливаем сохранённые маппинги (регистронезависимо)
        for mapping in self.current_mappings:
            src = mapping.get('source_field')
            if src in source_fields:
                row = source_fields.index(src)
                tgt = mapping.get('target_field')
                if tgt:
                    # Регистронезависимый поиск
                    combo = self.table.cellWidget(row, 1)
                    idx = -1
                    for i in range(combo.count()):
                        if combo.itemData(i) and combo.itemData(i).lower() == tgt.lower():
                            idx = i
                            break
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                if mapping.get('is_source_id'):
                    self.table.cellWidget(row, 2).setChecked(True)

        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_source_id_changed(self, changed_row, state):
        if state == Qt.Checked:
            for row in range(self.table.rowCount()):
                if row != changed_row:
                    self.table.cellWidget(row, 2).setChecked(False)

    def _on_accept(self):
        has_mapping = False
        source_id_row = None
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            tgt = combo.currentData()
            if tgt:
                has_mapping = True
            if self.table.cellWidget(row, 2).isChecked():
                source_id_row = row
        if not has_mapping:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Не выбрано ни одного сопоставления полей.")
            return
        if source_id_row is None:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Не указано ключевое поле источника (sourceid).")
            return

        self.mappings = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            tgt = combo.currentData()
            if tgt:
                src_field = self.source_fields[row]
                ref_info = self.source_refs.get(src_field, {})
                mapping = {
                    'source_field': src_field,
                    'target_field': tgt,
                    'is_source_id': self.table.cellWidget(row, 2).isChecked(),
                    'is_reference': ref_info.get('is_ref', False),
                    'ref_source_table': ref_info.get('ref_table', ''),
                    'ref_source_key_field': ref_info.get('ref_field', '')
                }
                self.mappings.append(mapping)
        self.accept()

    def get_mappings(self):
        return self.mappings