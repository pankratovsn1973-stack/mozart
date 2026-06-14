# mozart_import/designer/source_ref_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QCheckBox, QComboBox, QDialogButtonBox, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt


class SourceRefDialog(QDialog):
    """
    Диалог настройки ссылочных полей внутри таблицы источника.
    Для каждого поля можно указать, является ли оно ссылкой на другую таблицу источника,
    выбрать целевую таблицу и поле, которое служит ключом в этой таблице.
    """
    def __init__(self, source_table_name: str, source_fields: list, all_source_table_names: list,
                 current_refs: dict = None, parent=None):
        """
        source_fields -- список имён полей текущей таблицы
        all_source_table_names -- список имён всех таблиц источника (для выбора целевой таблицы)
        current_refs -- словарь {имя_поля: {'is_ref': bool, 'ref_table': str, 'ref_field': str}}
        """
        super().__init__(parent)
        self.setWindowTitle(f"Ссылочные поля таблицы «{source_table_name}»")
        self.resize(800, 400)

        self.source_fields = source_fields
        self.all_tables = all_source_table_names
        self.current_refs = current_refs or {}
        self.result_refs = {}

        layout = QVBoxLayout(self)

        self.table = QTableWidget(len(source_fields), 3)
        self.table.setHorizontalHeaderLabels(["Поле", "Ссылка?", "Целевая таблица.поле"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        for row, field_name in enumerate(source_fields):
            # Имя поля
            item = QTableWidgetItem(field_name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, item)

            # Чекбокс "Ссылка"
            chk = QCheckBox()
            ref_info = self.current_refs.get(field_name, {})
            chk.setChecked(ref_info.get('is_ref', False))
            self.table.setCellWidget(row, 1, chk)

            # Комбобокс с целевой таблицей и полем
            combo = QComboBox()
            for tbl in all_source_table_names:
                # Добавляем поля этой таблицы (упрощённо: предполагаем, что ключевое поле называется 'id' или первое поле)
                # В реальном приложении нужно знать схему всех таблиц, но здесь используем заглушку: поле 'id'
                combo.addItem(f"{tbl}.id", (tbl, 'id'))  # Пока предполагаем, что ключевое поле всегда 'id'
            # Если текущая ссылка уже установлена, выбираем соответствующий пункт
            if ref_info.get('is_ref'):
                target = ref_info.get('ref_table')
                field = ref_info.get('ref_field')
                idx = combo.findData((target, field))
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            self.table.setCellWidget(row, 2, combo)

        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _save(self):
        self.result_refs = {}
        for row in range(self.table.rowCount()):
            field_name = self.table.item(row, 0).text()
            is_ref = self.table.cellWidget(row, 1).isChecked()
            combo = self.table.cellWidget(row, 2)
            target_table, target_field = combo.currentData()
            self.result_refs[field_name] = {
                'is_ref': is_ref,
                'ref_table': target_table,
                'ref_field': target_field
            }
        self.accept()

    def get_refs(self):
        return self.result_refs