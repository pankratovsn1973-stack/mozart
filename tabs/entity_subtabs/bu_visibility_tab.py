# tabs/entity_subtabs/bu_visibility_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,                              QHeaderView, QMessageBox, QComboBox, QDialog,                              QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from database import DatabaseService
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator


class BUVISibilityTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_entity_id = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.crud = CrudButtons(self, with_add=True, with_edit=False, with_delete=True)
        layout.addWidget(self.crud)

        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.crud.add_clicked.connect(self.add_visibility)
        self.crud.delete_clicked.connect(self.delete_selected)

        self.retranslate_ui()

    def retranslate_ui(self):
        headers = [
            self.translator.tr('field_id'),
            self.translator.tr('field_balance_unit'),
            self.translator.tr('field_policy'),
            ""
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self, 'crud'):
            self.crud.retranslate_ui()
        self.load_data()

    def set_entity_id(self, entity_id):
        self.current_entity_id = entity_id
        self.load_data()

    def load_data(self):
        if not self.current_entity_id:
            self.table.setRowCount(0)
            return
        sql = """
            SELECT id, balanceunit_id, visibility_policy
            FROM meta.entitytype_visibility
            WHERE entitytype_id = %s
            ORDER BY id
        """
        rows = self.db.execute_query(sql, (self.current_entity_id,))
        self.table.setRowCount(0)
        policy_map = {
            'I': self.translator.tr('policy_individual'),
            'A': self.translator.tr('policy_all_visible'),
            'N': self.translator.tr('policy_all_hidden')
        }
        for r_idx, (vid, buid, policy) in enumerate(rows):
            self.table.insertRow(r_idx)
            # ID
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(vid)))
            # Балансовая единица
            bu_name = self.get_bu_name(buid)
            self.table.setItem(r_idx, 1, QTableWidgetItem(f"{bu_name} ({buid})"))
            # Политика
            self.table.setItem(r_idx, 2, QTableWidgetItem(policy_map.get(policy, policy)))
            self.table.item(r_idx, 0).setData(Qt.UserRole, vid)

    def get_bu_name(self, buid):
        res = self.db.execute_query("SELECT cname FROM auth.balanceunits WHERE id=%s", (buid,))
        return res[0][0] if res else str(buid)

    def get_bus_list(self):
        return self.db.execute_query("SELECT id, cname FROM auth.balanceunits ORDER BY cname")

    def add_visibility(self):
        if not self.current_entity_id:
            QMessageBox.warning(self, self.translator.tr('error'), self.translator.tr('warning_select_entity'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('title_add_visibility'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        bu_combo = QComboBox()
        for buid, buname in self.get_bus_list():
            bu_combo.addItem(f"{buname} ({buid})", buid)
        form.addRow(self.translator.tr('field_balance_unit'), bu_combo)

        policy_combo = QComboBox()
        policy_combo.addItem(self.translator.tr('policy_individual'), 'I')
        policy_combo.addItem(self.translator.tr('policy_all_visible'), 'A')
        policy_combo.addItem(self.translator.tr('policy_all_hidden'), 'N')
        form.addRow(self.translator.tr('field_policy'), policy_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText(self.translator.tr('btn_ok'))
        btn_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr('btn_cancel'))
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            buid = bu_combo.currentData()
            policy = policy_combo.currentData()
            check = self.db.execute_query(
                "SELECT id FROM meta.entitytype_visibility WHERE entitytype_id=%s AND balanceunit_id=%s",
                (self.current_entity_id, buid))
            if check:
                QMessageBox.warning(self, self.translator.tr('error'), self.translator.tr('error_visibility_exists'))
                return
            sql = "INSERT INTO meta.entitytype_visibility (entitytype_id, balanceunit_id, visibility_policy) VALUES (%s, %s, %s)"
            self.db.execute_query(sql, (self.current_entity_id, buid, policy), fetch=False)
            self.load_data()

    def delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_record'))
            return
        rows = set(item.row() for item in selected)
        ids = []
        for row in rows:
            vid_item = self.table.item(row, 0)
            if vid_item:
                ids.append(int(vid_item.text()))
        if not ids:
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                 self.translator.tr('confirm_delete_records') % len(ids),
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for vid in ids:
                self.db.execute_query("DELETE FROM meta.entitytype_visibility WHERE id=%s", (vid,), fetch=False)
            self.load_data()