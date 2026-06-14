# tabs/entity_subtabs/fields_tab.py
# -*- coding: utf-8 -*-
# Модуль: Вкладка "Поля" для сущности (конфигуратор)
# Исправление: системные сущности — только просмотр полей

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush
from database import DatabaseService
from crud_buttons import CrudButtons
from ide_field_edit import FieldEditDialog, SYSTEM_FIELDS
from lang.local_translator import LocalTranslator


class FieldsTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_entity_id = None
        self.is_system = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.crud = CrudButtons(self)
        layout.addWidget(self.crud)

        self.table = QTableWidget(0, 9)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.crud.add_clicked.connect(self.add_field)
        self.crud.edit_clicked.connect(self.edit_field)
        self.crud.delete_clicked.connect(self.delete_selected_fields)

        self.retranslate_ui()

    def retranslate_ui(self):
        headers = [
            '',  # чекбокс
            self.translator.tr('field_name'),
            self.translator.tr('field_type'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_description'),
            self.translator.tr('field_length'),
            self.translator.tr('field_decimals'),
            self.translator.tr('field_index'),
            self.translator.tr('field_ref_type'),
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, False)
        if hasattr(self, 'crud'):
            self.crud.retranslate_ui()
        self._update_crud_visibility()

    def set_entity_id(self, entity_id, is_system=False):
        self.current_entity_id = entity_id
        self.is_system = is_system
        self._update_crud_visibility()
        self.load_fields()

    def _update_crud_visibility(self):
        """Скрываем кнопки CRUD для системных сущностей."""
        if hasattr(self, 'crud'):
            self.crud.setVisible(not self.is_system)

    def load_fields(self):
        if not self.current_entity_id:
            self.table.setRowCount(0)
            return

        # Загружаем все поля, включая информацию о системности
        sql = """
            SELECT f.cfieldname, t.cname, f.calias, f.mcomment,
                   f.nlength, f.ndecimals, f.lisindexed,
                   CASE WHEN f.ref_entitytypeid IS NOT NULL 
                        THEN (SELECT cname FROM meta.entitytypes WHERE id = f.ref_entitytypeid)
                        ELSE NULL END as ref_name,
                   f.cfieldtype, f.ref_entitytypeid, f.status_id, f.is_system,
                   (SELECT class_id FROM meta.entitytypes WHERE id = f.ref_entitytypeid) as ref_class_id
            FROM meta.fields f
            JOIN meta.field_types t ON f.cfieldtype = t.ccode
            WHERE f.entitytypeid = %s
            ORDER BY f.isortorder
        """
        rows = self.db.execute_query(sql, (self.current_entity_id,))
        self.table.setRowCount(0)

        for r_idx, row in enumerate(rows):
            field_name = row[0]
            is_field_system = row[11] if len(row) > 11 else (field_name in SYSTEM_FIELDS)

            self.table.insertRow(r_idx)

            # Колонка 0: чекбокс
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if row[10] == 2 or self.is_system or is_field_system:
                chk_item.setFlags(chk_item.flags() & ~Qt.ItemIsEnabled)
                chk_item.setBackground(QBrush(Qt.lightGray))
            chk_item.setCheckState(Qt.Unchecked)
            chk_item.setData(Qt.UserRole, row[10])
            chk_item.setData(Qt.UserRole + 1, is_field_system)
            self.table.setItem(r_idx, 0, chk_item)

            # Колонки 1-8
            for c_idx in range(8):
                if c_idx == 7:
                    val = row[7] if row[7] else ""
                elif c_idx == 1:
                    val = row[0]  # в колонке "тип" показываем cfieldname? Нет, row[c_idx]
                    val = row[c_idx] if row[c_idx] else ""
                else:
                    val = row[c_idx] if row[c_idx] is not None else ""

                item = QTableWidgetItem(str(val))
                if c_idx == 1:
                    item.setData(Qt.UserRole, row[8])  # код типа
                self.table.setItem(r_idx, c_idx + 1, item)

    def add_field(self):
        if self.is_system:
            return
        if not self.current_entity_id:
            QMessageBox.warning(self, self.translator.tr('error'), self.translator.tr('warning_select_entity'))
            return
        dlg = FieldEditDialog(db=self.db, is_system=False)
        if dlg.exec_():
            data = dlg.get_data()
            self._save_field(data)

    def edit_field(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, self.translator.tr('error'), self.translator.tr('warning_select_field'))
            return
        row = selected[0].row()
        field_name = self.table.item(row, 1).text()

        # Проверяем, системное ли поле
        chk_item = self.table.item(row, 0)
        is_field_system = chk_item.data(Qt.UserRole + 1) if chk_item else False

        # Для системной сущности — только просмотр
        if self.is_system:
            self._view_field(row)
            return

        # Для системного поля — только просмотр
        if is_field_system:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                f"Поле '{field_name}' является системным и не редактируется")
            self._view_field(row)
            return

        type_code = self.table.item(row, 2).data(Qt.UserRole)
        ref_entity = self.table.item(row, 8).text() if self.table.item(row, 8) else ""

        data = [
            field_name,
            type_code,
            self.table.item(row, 3).text(),
            self.table.item(row, 4).text(),
            self.table.item(row, 5).text(),
            self.table.item(row, 6).text(),
            self.table.item(row, 7).text() == self.translator.tr('yes'),
            ref_entity if ref_entity else None,
            None,
            is_field_system,
            None
        ]
        status_id = chk_item.data(Qt.UserRole) if chk_item else 1
        read_only = (status_id == 2)
        dlg = FieldEditDialog(data, status_id=status_id, read_only_mode=read_only, is_system=is_field_system, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            self._save_field(new_data, is_update=True, old_name=field_name)

    def _view_field(self, row):
        """Только просмотр поля (для системных сущностей/полей)."""
        field_name = self.table.item(row, 1).text()
        type_code = self.table.item(row, 2).data(Qt.UserRole)
        ref_entity = self.table.item(row, 8).text() if self.table.item(row, 8) else ""

        data = [
            field_name,
            type_code,
            self.table.item(row, 3).text(),
            self.table.item(row, 4).text(),
            self.table.item(row, 5).text(),
            self.table.item(row, 6).text(),
            self.table.item(row, 7).text() == self.translator.tr('yes'),
            ref_entity if ref_entity else None,
            None,
            False,
            None
        ]
        dlg = FieldEditDialog(data, read_only_mode=True, is_system=True, db=self.db)
        dlg.exec_()

    def delete_selected_fields(self):
        if self.is_system:
            return

        selected_rows = set()
        prod_names = []
        dev_ids = []
        system_fields = []

        for item in self.table.selectedItems():
            row = item.row()
            if row not in selected_rows:
                selected_rows.add(row)
                chk_item = self.table.item(row, 0)
                status_id = chk_item.data(Qt.UserRole) if chk_item else 1
                is_field_system = chk_item.data(Qt.UserRole + 1) if chk_item else False
                fname = self.table.item(row, 1).text()

                if is_field_system:
                    system_fields.append(fname)
                    continue

                if status_id == 1:
                    dev_ids.append((self.current_entity_id, fname))
                else:
                    prod_names.append(fname)

        if system_fields:
            QMessageBox.critical(self, self.translator.tr('error'),
                                 f"Системные поля нельзя удалять: {', '.join(system_fields)}")
            return

        if prod_names:
            QMessageBox.critical(self, self.translator.tr('error'),
                                 self.translator.tr('error_prod_field_delete') + "\n" + ", ".join(prod_names))
            return

        if not dev_ids:
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_fields') % len(dev_ids),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for eid, fname in dev_ids:
                self.db.execute_query("DELETE FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
                                      (eid, fname), fetch=False)
            self.load_fields()

    def _save_field(self, field_data, is_update=False, old_name=None):
        if self.is_system:
            return

        entitytypeid = self.current_entity_id
        if not entitytypeid:
            QMessageBox.warning(self, self.translator.tr('error'), self.translator.tr('warning_select_entity'))
            return

        cfieldname = field_data[0]
        cfieldtype = field_data[1]
        calias = field_data[2]
        mcomment = field_data[3]
        nlength = field_data[4]
        ndecimals = field_data[5]
        lisindexed = field_data[6]
        ref_entitytypeid = field_data[7]
        status_id = field_data[8]
        is_field_system = field_data[9] if len(field_data) > 9 else False
        ref_class_id = field_data[10] if len(field_data) > 10 else None

        try:
            if is_update:
                if old_name and old_name != cfieldname:
                    sql_table = "SELECT cname FROM meta.entitytypes WHERE id = %s"
                    res = self.db.execute_query(sql_table, (entitytypeid,))
                    if res:
                        ext_table = f"ext.ext_{res[0][0]}"
                        rename_sql = f"ALTER TABLE {ext_table} RENAME COLUMN {old_name} TO {cfieldname}"
                        self.db.execute_query(rename_sql, fetch=False)
                sql = """UPDATE meta.fields SET
                            cfieldname=%s, cfieldtype=%s, calias=%s, mcomment=%s,
                            nlength=%s, ndecimals=%s, lisindexed=%s, ref_entitytypeid=%s, status_id=%s, is_system=%s
                         WHERE entitytypeid=%s AND cfieldname=%s"""
                self.db.execute_query(sql, (cfieldname, cfieldtype, calias, mcomment,
                                            nlength, ndecimals, lisindexed, ref_entitytypeid, status_id, is_field_system,
                                            entitytypeid, old_name), fetch=False)
            else:
                if cfieldtype == 'R' and not ref_entitytypeid and ref_class_id:
                    sql = """INSERT INTO meta.fields
                                (entitytypeid, cfieldname, cfieldtype, calias, mcomment,
                                 nlength, ndecimals, lisindexed, ref_entitytypeid, status_id, is_system)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"""
                    res = self.db.execute_query(sql, (entitytypeid, cfieldname, cfieldtype, calias, mcomment,
                                                      nlength, ndecimals, lisindexed, None, status_id, is_field_system))
                else:
                    sql = """INSERT INTO meta.fields
                                (entitytypeid, cfieldname, cfieldtype, calias, mcomment,
                                 nlength, ndecimals, lisindexed, ref_entitytypeid, status_id, is_system)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"""
                    res = self.db.execute_query(sql, (entitytypeid, cfieldname, cfieldtype, calias, mcomment,
                                                      nlength, ndecimals, lisindexed, ref_entitytypeid, status_id,
                                                      is_field_system))
                if res:
                    field_id = res[0][0]
                    if not is_field_system:
                        self.db.execute_procedure("meta.p_field_sync", (field_id,))
            self.load_fields()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), self.translator.tr('error_save_field') + str(e))