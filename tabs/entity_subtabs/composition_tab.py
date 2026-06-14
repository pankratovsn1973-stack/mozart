# tabs/entity_subtabs/composition_tab.py
# -*- coding: utf-8 -*-
# Модуль: Вкладка "Подчинённые таблицы" (конфигуратор)
# Исправление: системные связи (роль FILES) — только просмотр, нельзя удалить/редактировать

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,                              QHeaderView, QMessageBox, QTabWidget, QDialog,                              QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush
from database import DatabaseService
from crud_buttons import CrudButtons
from composition_manager import CompositionManager
from lang.local_translator import LocalTranslator

SYSTEM_COMPOSITION_ROLES = ['FILES']


class CompositionTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.composition_manager = CompositionManager(db=self.db, parent_widget=self)
        self.current_entity_id = None
        self.is_system = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.parent_tab = self._create_parent_tab()
        self.tabs.addTab(self.parent_tab, self.translator.tr('tab_as_parent'))

        self.child_tab = self._create_child_tab()
        self.tabs.addTab(self.child_tab, self.translator.tr('tab_as_child'))

        self.retranslate_ui()

    def retranslate_ui(self):
        self.tabs.setTabText(0, self.translator.tr('tab_as_parent'))
        self.tabs.setTabText(1, self.translator.tr('tab_as_child'))
        self.parent_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_detail'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field'),
            self.translator.tr('field_order')
        ])
        self.child_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_master'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field'),
            self.translator.tr('field_order')
        ])
        if hasattr(self, 'parent_crud'):
            self.parent_crud.retranslate_ui()
        if hasattr(self, 'child_crud'):
            self.child_crud.retranslate_ui()

    def _create_parent_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.parent_crud = CrudButtons(self, with_add=True, with_edit=True, with_delete=True)
        layout.addWidget(self.parent_crud)
        self.parent_table = QTableWidget(0, 6)  # добавили колонку для system_role
        self.parent_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_detail'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field'),
            self.translator.tr('field_order'),
            ''  # скрытая колонка для role_calias
        ])
        self.parent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parent_table.setColumnHidden(5, True)  # скрываем колонку с calias
        self.parent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parent_table.itemDoubleClicked.connect(lambda: self.edit_composition('parent'))
        layout.addWidget(self.parent_table)
        self.parent_crud.add_clicked.connect(lambda: self.add_composition('parent'))
        self.parent_crud.edit_clicked.connect(lambda: self.edit_composition('parent'))
        self.parent_crud.delete_clicked.connect(lambda: self.delete_composition('parent'))
        return tab

    def _create_child_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.child_crud = CrudButtons(self, with_add=False, with_edit=True, with_delete=True)
        layout.addWidget(self.child_crud)
        self.child_table = QTableWidget(0, 6)
        self.child_table.setHorizontalHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_master'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field'),
            self.translator.tr('field_order'),
            ''
        ])
        self.child_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.child_table.setColumnHidden(5, True)
        self.child_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.child_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.child_table.itemDoubleClicked.connect(lambda: self.edit_composition('child'))
        layout.addWidget(self.child_table)
        self.child_crud.edit_clicked.connect(lambda: self.edit_composition('child'))
        self.child_crud.delete_clicked.connect(lambda: self.delete_composition('child'))
        return tab

    def set_entity_id(self, entity_id, is_system=False):
        self.current_entity_id = entity_id
        self.is_system = is_system
        self._update_crud_visibility()
        self.load_parent()
        self.load_child()

    def _update_crud_visibility(self):
        if hasattr(self, 'parent_crud'):
            self.parent_crud.setVisible(not self.is_system)
        if hasattr(self, 'child_crud'):
            self.child_crud.setVisible(not self.is_system)

    def _is_system_role(self, role_calias):
        """Проверяет, является ли роль системной (нельзя редактировать/удалять)."""
        return role_calias in SYSTEM_COMPOSITION_ROLES

    def load_parent(self):
        if not self.current_entity_id:
            self.parent_table.setRowCount(0)
            return
        sql = """
            SELECT c.id, et.cname, cr.cname, c.c_link_fieldname, c.isortorder, cr.calias
            FROM meta.entity_composition c
            JOIN meta.entitytypes et ON c.child_entityid = et.id
            JOIN meta.composition_roles cr ON c.role_id = cr.id
            WHERE c.parent_entityid = %s
            ORDER BY c.id
        """
        rows = self.db.execute_query(sql, (self.current_entity_id,))
        self.parent_table.setRowCount(0)
        for r_idx, (cid, child, role, field, order, role_calias) in enumerate(rows):
            self.parent_table.insertRow(r_idx)
            self.parent_table.setItem(r_idx, 0, QTableWidgetItem(str(cid)))
            self.parent_table.setItem(r_idx, 1, QTableWidgetItem(child))
            self.parent_table.setItem(r_idx, 2, QTableWidgetItem(role))
            self.parent_table.setItem(r_idx, 3, QTableWidgetItem(field))
            self.parent_table.setItem(r_idx, 4, QTableWidgetItem(str(order)))
            self.parent_table.setItem(r_idx, 5, QTableWidgetItem(role_calias or ''))

            is_sys = self._is_system_role(role_calias)
            if is_sys or self.is_system:
                for col in range(6):
                    item = self.parent_table.item(r_idx, col)
                    if item:
                        item.setForeground(QBrush(Qt.darkCyan))

            self.parent_table.item(r_idx, 0).setData(Qt.UserRole, cid)
            self.parent_table.item(r_idx, 0).setData(Qt.UserRole + 1, is_sys)

    def load_child(self):
        if not self.current_entity_id:
            self.child_table.setRowCount(0)
            return
        sql = """
            SELECT c.id, et.cname, cr.cname, c.c_link_fieldname, c.isortorder, cr.calias
            FROM meta.entity_composition c
            JOIN meta.entitytypes et ON c.parent_entityid = et.id
            JOIN meta.composition_roles cr ON c.role_id = cr.id
            WHERE c.child_entityid = %s
            ORDER BY c.id
        """
        rows = self.db.execute_query(sql, (self.current_entity_id,))
        self.child_table.setRowCount(0)
        for r_idx, (cid, master, role, field, order, role_calias) in enumerate(rows):
            self.child_table.insertRow(r_idx)
            self.child_table.setItem(r_idx, 0, QTableWidgetItem(str(cid)))
            self.child_table.setItem(r_idx, 1, QTableWidgetItem(master))
            self.child_table.setItem(r_idx, 2, QTableWidgetItem(role))
            self.child_table.setItem(r_idx, 3, QTableWidgetItem(field))
            self.child_table.setItem(r_idx, 4, QTableWidgetItem(str(order)))
            self.child_table.setItem(r_idx, 5, QTableWidgetItem(role_calias or ''))

            is_sys = self._is_system_role(role_calias)
            if is_sys or self.is_system:
                for col in range(6):
                    item = self.child_table.item(r_idx, col)
                    if item:
                        item.setForeground(QBrush(Qt.darkCyan))

            self.child_table.item(r_idx, 0).setData(Qt.UserRole, cid)
            self.child_table.item(r_idx, 0).setData(Qt.UserRole + 1, is_sys)

    def add_composition(self, role):
        if self.is_system:
            return
        if role == 'parent':
            if not self.current_entity_id:
                QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_entity'))
                return
            dlg = QDialog(self)
            dlg.setWindowTitle(self.translator.tr('title_add_composition'))
            layout = QVBoxLayout(dlg)
            form = QFormLayout()
            entities = self.db.execute_query("SELECT id, cname FROM meta.entitytypes WHERE id != %s ORDER BY cname",
                                             (self.current_entity_id,))
            child_combo = QComboBox()
            for eid, ename in entities:
                child_combo.addItem(f"{ename} ({eid})", eid)
            form.addRow(self.translator.tr('field_detail'), child_combo)
            roles = self.db.execute_query("SELECT id, cname FROM meta.composition_roles ORDER BY cname")
            role_combo = QComboBox()
            for rid, rname in roles:
                role_combo.addItem(f"{rname} ({rid})", rid)
            form.addRow(self.translator.tr('field_role'), role_combo)
            field_edit = QLineEdit()
            form.addRow(self.translator.tr('field_link_field'), field_edit)
            order_edit = QLineEdit("10")
            form.addRow(self.translator.tr('field_order'), order_edit)
            layout.addLayout(form)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dlg.accept)
            btn_box.rejected.connect(dlg.reject)
            layout.addWidget(btn_box)
            if dlg.exec_() == QDialog.Accepted:
                child_id = child_combo.currentData()
                role_id = role_combo.currentData()
                field = field_edit.text()
                order = int(order_edit.text()) if order_edit.text().isdigit() else 10
                success = self.composition_manager.add_composition(
                    parent_entityid=self.current_entity_id,
                    child_entityid=child_id,
                    role_id=role_id,
                    link_field=field,
                    sortorder=order
                )
                if success:
                    self.load_parent()
        else:
            QMessageBox.information(self, self.translator.tr('info'),
                                    self.translator.tr('info_add_as_child_not_supported'))

    def edit_composition(self, mode):
        if self.is_system:
            return

        table = self.parent_table if mode == 'parent' else self.child_table
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_record'))
            return
        row = selected[0].row()
        cid = table.item(row, 0).data(Qt.UserRole)
        is_sys = table.item(row, 0).data(Qt.UserRole + 1)

        if is_sys:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Системные связи нельзя редактировать")
            return

        sql = """SELECT parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder
                 FROM meta.entity_composition WHERE id=%s"""
        row_data = self.db.execute_query(sql, (cid,))
        if not row_data:
            return
        parent, child, role, field, order = row_data[0]
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('title_edit_composition'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        if mode == 'parent':
            entities = self.db.execute_query("SELECT id, cname FROM meta.entitytypes WHERE id != %s ORDER BY cname",
                                             (self.current_entity_id,))
            child_combo = QComboBox()
            for eid, ename in entities:
                child_combo.addItem(f"{ename} ({eid})", eid)
            idx = child_combo.findData(child)
            if idx >= 0:
                child_combo.setCurrentIndex(idx)
            form.addRow(self.translator.tr('field_detail'), child_combo)
        else:
            parent_name = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (parent,))[0][0]
            form.addRow(self.translator.tr('field_master'), QLabel(f"{parent_name} ({parent})"))
        roles = self.db.execute_query("SELECT id, cname FROM meta.composition_roles ORDER BY cname")
        role_combo = QComboBox()
        for rid, rname in roles:
            role_combo.addItem(f"{rname} ({rid})", rid)
        idx = role_combo.findData(role)
        if idx >= 0:
            role_combo.setCurrentIndex(idx)
        form.addRow(self.translator.tr('field_role'), role_combo)
        field_edit = QLineEdit(field)
        form.addRow(self.translator.tr('field_link_field'), field_edit)
        order_edit = QLineEdit(str(order))
        form.addRow(self.translator.tr('field_order'), order_edit)
        layout.addLayout(form)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_() == QDialog.Accepted:
            new_role = role_combo.currentData()
            new_field = field_edit.text()
            new_order = int(order_edit.text()) if order_edit.text().isdigit() else 10
            if mode == 'parent':
                new_child = child_combo.currentData()
                success = self.composition_manager.update_composition(
                    comp_id=cid,
                    parent_entityid=self.current_entity_id,
                    child_entityid=new_child,
                    role_id=new_role,
                    link_field=new_field,
                    sortorder=new_order
                )
                if success:
                    self.load_parent()
            else:
                success = self.composition_manager.update_composition(
                    comp_id=cid,
                    parent_entityid=parent,
                    child_entityid=self.current_entity_id,
                    role_id=new_role,
                    link_field=new_field,
                    sortorder=new_order
                )
                if success:
                    self.load_child()

    def delete_composition(self, mode):
        if self.is_system:
            return

        table = self.parent_table if mode == 'parent' else self.child_table
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_record'))
            return
        rows = set(item.row() for item in selected)
        ids = []
        sys_ids = []
        for row in rows:
            cid_item = table.item(row, 0)
            if cid_item:
                cid = cid_item.data(Qt.UserRole)
                is_sys = cid_item.data(Qt.UserRole + 1)
                if is_sys:
                    sys_ids.append(cid)
                else:
                    ids.append(cid)

        if sys_ids:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                f"Системные связи нельзя удалить (id: {', '.join(map(str, sys_ids))})")
            return
        if not ids:
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_records') % len(ids),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for cid in ids:
                self.composition_manager.delete_composition(cid)
            self.load_parent()
            self.load_child()