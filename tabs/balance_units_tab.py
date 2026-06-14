


# tabs/balance_units_tab.py
# tabs/balance_units_tab.py
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QCheckBox
from PySide6.QtCore import Qt
from .base_tab import BaseTab
from crud_buttons import CrudButtons
from widgets import ReferenceEditor
from lang.local_translator import LocalTranslator


class BalanceUnitEditDialog(QDialog):
    def __init__(self, parent=None, data=None, db=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('title_edit_balance_unit'))
        self.data = data or {}
        self.db = db
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))
        self.ref_parent = ReferenceEditor(
            table_name='auth.balanceunits',
            display_field='cname',
            db=self.db
        )
        if self.data.get("parentid"):
            sql = "SELECT cname FROM auth.balanceunits WHERE id = %s"
            res = self.db.execute_query(sql, (self.data["parentid"],))
            if res:
                self.ref_parent.set_value(self.data["parentid"], res[0][0])
        self.chk_is_bu = QCheckBox(self.translator.tr('label_is_balance_unit'))
        self.chk_is_bu.setChecked(self.data.get("lisbalanceunit", True))

        form.addRow(self.translator.tr('field_name'), self.edit_name)
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)
        form.addRow(self.translator.tr('field_parent'), self.ref_parent)
        form.addRow(self.chk_is_bu)

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
            "parentid": self.ref_parent.get_value(),
            "lisbalanceunit": self.chk_is_bu.isChecked()
        }


class BalanceUnitsTab(BaseTab):
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)

        self.crud = CrudButtons(self)
        self.layout.addWidget(self.crud)

        self.tree = QTreeWidget()
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 100)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        self.layout.addWidget(self.tree)

        self.crud.add_clicked.connect(self.add_item)
        self.crud.edit_clicked.connect(self.edit_item)
        self.crud.delete_clicked.connect(self.delete_item)

        self.retranslate_ui()   # устанавливаем заголовки при старте
        self.load_data()

    def retranslate_ui(self):
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_active')
        ])
        if hasattr(self, 'crud'):
            self.crud.retranslate_ui()


    def load_data(self):
        sql = "SELECT id, parentid, level, data FROM get_hierarchy_iterative(%s, %s, %s)"
        rows = self.db.execute_query(sql, ('auth.balanceunits', 'id', 'parentid'))

        self.tree.clear()
        items = {}

        for row in rows:
            node_id, parent_id, level, data = row
            name = data.get('cname', '')
            alias = data.get('calias', '')
            is_active = data.get('lisbalanceunit', False)

            item = QTreeWidgetItem()
            item.setText(0, str(node_id))
            item.setText(1, name)
            item.setText(2, alias if alias else "")
            item.setText(3, "Да" if is_active else "Нет")
            item.setData(0, Qt.UserRole, node_id)
            items[node_id] = item

            if parent_id is None:
                self.tree.addTopLevelItem(item)
            else:
                if parent_id in items:
                    items[parent_id].addChild(item)
                else:
                    self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def get_selected_id(self):
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def add_item(self):
        dlg = BalanceUnitEditDialog(self, db=self.db)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO auth.balanceunits (cname, calias, parentid, lisbalanceunit)
                     VALUES (%s, %s, %s, %s)"""
            self.db.execute_query(sql, (data["cname"], data["calias"], data["parentid"], data["lisbalanceunit"]), fetch=False)
            self.load_data()

    def edit_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            self.show_warning(translator.tr("warn_select_record_edit"))
            return
        sql = "SELECT cname, calias, parentid, lisbalanceunit FROM auth.balanceunits WHERE id=%s"
        row = self.db.execute_query(sql, (item_id,))
        if not row:
            return
        data = {
            "cname": row[0][0],
            "calias": row[0][1],
            "parentid": row[0][2],
            "lisbalanceunit": row[0][3]
        }
        dlg = BalanceUnitEditDialog(self, data, db=self.db)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """UPDATE auth.balanceunits SET cname=%s, calias=%s, parentid=%s, lisbalanceunit=%s WHERE id=%s"""
            self.db.execute_query(sql, (new_data["cname"], new_data["calias"], new_data["parentid"], new_data["lisbalanceunit"], item_id), fetch=False)
            self.load_data()

    def delete_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            self.show_warning(translator.tr("warn_select_record_delete"))
            return
        if QMessageBox.question(self, translator.tr("confirm_title"), translator.tr("confirm_delete_record")) == QMessageBox.Yes:
            sql = "DELETE FROM auth.balanceunits WHERE id=%s"
            self.db.execute_query(sql, (item_id,), fetch=False)
            self.load_data()