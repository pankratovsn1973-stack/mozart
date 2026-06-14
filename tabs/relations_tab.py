



# tabs/relations_tab.py
from PySide6.QtWidgets import (QWidget, QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget,                              QTableWidgetItem, QPushButton, QHBoxLayout, QVBoxLayout,                              QMessageBox, QDialog, QFormLayout, QLineEdit,                              QComboBox, QLabel, QHeaderView)
from PySide6.QtCore import Qt
from .base_tab import BaseTab
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator


class RefTypeEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle(translator.tr("title_ref_type"))
        self.data = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_name = QLineEdit(self.data.get("cname", ""))
        self.edit_alias = QLineEdit(self.data.get("calias", ""))
        self.edit_comment = QLineEdit(self.data.get("mcomment", ""))
        form.addRow("Наименование:", self.edit_name)
        form.addRow("Алиас:", self.edit_alias)
        form.addRow("Комментарий:", self.edit_comment)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "cname": self.edit_name.text(),
            "calias": self.edit_alias.text(),
            "mcomment": self.edit_comment.text()
        }


class RefRuleEditDialog(QDialog):
    def __init__(self, parent=None, data=None, ref_types=None, entity_types=None):
        super().__init__(parent)
        self.setWindowTitle(translator.tr("title_ref_rule"))
        self.data = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_ref_type = QComboBox()
        for tid, tname in ref_types or []:
            self.combo_ref_type.addItem(f"{tname} ({tid})", tid)
        self.combo_entity = QComboBox()
        for eid, ename in entity_types or []:
            self.combo_entity.addItem(f"{ename} ({eid})", eid)
        self.combo_role_source = QComboBox()
        for eid, ename in entity_types or []:
            self.combo_role_source.addItem(f"{ename} ({eid})", eid)

        if data:
            idx = self.combo_ref_type.findData(data.get("reftypeid"))
            if idx >= 0: self.combo_ref_type.setCurrentIndex(idx)
            idx = self.combo_entity.findData(data.get("entitytypeid"))
            if idx >= 0: self.combo_entity.setCurrentIndex(idx)
            idx = self.combo_role_source.findData(data.get("role_source_entityid"))
            if idx >= 0: self.combo_role_source.setCurrentIndex(idx)

        form.addRow("Тип связи:", self.combo_ref_type)
        form.addRow("Тип сущности-участника:", self.combo_entity)
        form.addRow("Источник ролей:", self.combo_role_source)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "reftypeid": self.combo_ref_type.currentData(),
            "entitytypeid": self.combo_entity.currentData(),
            "role_source_entityid": self.combo_role_source.currentData()
        }


class RelationsTab(BaseTab):
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Вкладка "Типы связей"
        self.types_tab = self._create_types_tab()
        self.tabs.addTab(self.types_tab, "Типы связей")

        # Вкладка "Правила"
        self.rules_tab = self._create_rules_tab()
        self.tabs.addTab(self.rules_tab, "Правила")

        # Вкладка "Экземпляры связей" (заглушка)
        self.instances_tab = self._create_instances_tab()
        self.tabs.addTab(self.instances_tab, "Экземпляры связей")

    def _create_types_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.type_crud = CrudButtons(self)
        layout.addWidget(self.type_crud)
        self.type_table = QTableWidget()
        self.type_table.setColumnCount(3)
        self.type_table.setHorizontalHeaderLabels(["ID", "Алиас", "Наименование"])
        self.type_table.horizontalHeader().setStretchLastSection(True)
        self.type_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.type_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.type_table.itemDoubleClicked.connect(self.edit_type)
        layout.addWidget(self.type_table)
        self.type_crud.add_clicked.connect(self.add_type)
        self.type_crud.edit_clicked.connect(self.edit_type)
        self.type_crud.delete_clicked.connect(self.delete_type)
        self._load_types()
        return tab

    def _create_rules_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.rule_crud = CrudButtons(self)
        layout.addWidget(self.rule_crud)
        self.rule_table = QTableWidget()
        self.rule_table.setColumnCount(4)
        self.rule_table.setHorizontalHeaderLabels(["ID", "Тип связи", "Тип участника", "Источник ролей"])
        self.rule_table.horizontalHeader().setStretchLastSection(True)
        self.rule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rule_table.itemDoubleClicked.connect(self.edit_rule)
        layout.addWidget(self.rule_table)
        self.rule_crud.add_clicked.connect(self.add_rule)
        self.rule_crud.edit_clicked.connect(self.edit_rule)
        self.rule_crud.delete_clicked.connect(self.delete_rule)
        self._load_rules()
        return tab

    def _create_instances_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Раздел в разработке: просмотр и редактирование экземпляров связей."))
        return tab

    # --- Типы связей ---
    def _load_types(self):
        sql = "SELECT id, calias, cname FROM meta.entity_ref_types ORDER BY id"
        rows = self.db.execute_query(sql)
        self.type_table.setRowCount(0)
        for row in rows:
            pos = self.type_table.rowCount()
            self.type_table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 0:
                    item.setData(Qt.UserRole, val)
                self.type_table.setItem(pos, col, item)

    def add_type(self):
        dlg = RefTypeEditDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            sql = "INSERT INTO meta.entity_ref_types (calias, cname, mcomment) VALUES (%s, %s, %s)"
            self.db.execute_query(sql, (data["calias"], data["cname"], data["mcomment"]), fetch=False)
            self._load_types()

    def edit_type(self):
        row = self.type_table.currentRow()
        if row < 0:
            self.show_warning(translator.tr("warn_select_ref_type"))
            return
        item = self.type_table.item(row, 0)
        tid = item.data(Qt.UserRole)
        sql = "SELECT calias, cname, mcomment FROM meta.entity_ref_types WHERE id=%s"
        row_data = self.db.execute_query(sql, (tid,))
        if not row_data:
            return
        data = {
            "calias": row_data[0][0],
            "cname": row_data[0][1],
            "mcomment": row_data[0][2]
        }
        dlg = RefTypeEditDialog(self, data)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = "UPDATE meta.entity_ref_types SET calias=%s, cname=%s, mcomment=%s WHERE id=%s"
            self.db.execute_query(sql, (new_data["calias"], new_data["cname"], new_data["mcomment"], tid), fetch=False)
            self._load_types()

    def delete_type(self):
        row = self.type_table.currentRow()
        if row < 0:
            self.show_warning(translator.tr("warn_select_ref_type"))
            return
        item = self.type_table.item(row, 0)
        tid = item.data(Qt.UserRole)
        if QMessageBox.question(self, translator.tr("confirm_title"), "Удалить тип связи?") == QMessageBox.Yes:
            sql = "DELETE FROM meta.entity_ref_types WHERE id=%s"
            self.db.execute_query(sql, (tid,), fetch=False)
            self._load_types()

    # --- Правила ---
    def _load_rules(self):
        sql = """SELECT r.id, rt.cname, et.cname, rs.cname
                 FROM meta.entity_ref_rules r
                 JOIN meta.entity_ref_types rt ON r.reftypeid = rt.id
                 JOIN meta.entitytypes et ON r.entitytypeid = et.id
                 JOIN meta.entitytypes rs ON r.role_source_entityid = rs.id
                 ORDER BY r.id"""
        rows = self.db.execute_query(sql)
        self.rule_table.setRowCount(0)
        for row in rows:
            pos = self.rule_table.rowCount()
            self.rule_table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 0:
                    item.setData(Qt.UserRole, row[0])
                self.rule_table.setItem(pos, col, item)

    def get_ref_types_list(self):
        sql = "SELECT id, cname FROM meta.entity_ref_types ORDER BY cname"
        return self.db.execute_query(sql)

    def get_entity_types_list(self):
        sql = "SELECT id, cname FROM meta.entitytypes ORDER BY cname"
        return self.db.execute_query(sql)

    def add_rule(self):
        ref_types = self.get_ref_types_list()
        entity_types = self.get_entity_types_list()
        dlg = RefRuleEditDialog(self, ref_types=ref_types, entity_types=entity_types)
        if dlg.exec_():
            data = dlg.get_data()
            sql = """INSERT INTO meta.entity_ref_rules (reftypeid, entitytypeid, role_source_entityid)
                     VALUES (%s, %s, %s)"""
            self.db.execute_query(sql, (data["reftypeid"], data["entitytypeid"], data["role_source_entityid"]), fetch=False)
            self._load_rules()

    def edit_rule(self):
        row = self.rule_table.currentRow()
        if row < 0:
            self.show_warning(translator.tr("warn_select_rule"))
            return
        item = self.rule_table.item(row, 0)
        rid = item.data(Qt.UserRole)
        sql = "SELECT reftypeid, entitytypeid, role_source_entityid FROM meta.entity_ref_rules WHERE id=%s"
        row_data = self.db.execute_query(sql, (rid,))
        if not row_data:
            return
        data = {
            "reftypeid": row_data[0][0],
            "entitytypeid": row_data[0][1],
            "role_source_entityid": row_data[0][2]
        }
        ref_types = self.get_ref_types_list()
        entity_types = self.get_entity_types_list()
        dlg = RefRuleEditDialog(self, data, ref_types, entity_types)
        if dlg.exec_():
            new_data = dlg.get_data()
            sql = """UPDATE meta.entity_ref_rules SET
                        reftypeid=%s, entitytypeid=%s, role_source_entityid=%s
                     WHERE id=%s"""
            self.db.execute_query(sql, (new_data["reftypeid"], new_data["entitytypeid"],
                                        new_data["role_source_entityid"], rid), fetch=False)
            self._load_rules()

    def delete_rule(self):
        row = self.rule_table.currentRow()
        if row < 0:
            self.show_warning(translator.tr("warn_select_rule"))
            return
        item = self.rule_table.item(row, 0)
        rid = item.data(Qt.UserRole)
        if QMessageBox.question(self, translator.tr("confirm_title"), "Удалить правило?") == QMessageBox.Yes:
            sql = "DELETE FROM meta.entity_ref_rules WHERE id=%s"
            self.db.execute_query(sql, (rid,), fetch=False)
            self._load_rules()