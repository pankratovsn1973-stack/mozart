# tabs/class_templates_tab.py
# -*- coding: utf-8 -*-
# Модуль: Шаблоны классов (поля + дочерние таблицы)
# Версия: 2.2 — все заголовки обновляются при смене языка

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,                              QTableWidgetItem, QPushButton, QMessageBox, QHeaderView,                              QComboBox, QDialog, QFormLayout, QLineEdit, QCheckBox,                              QDialogButtonBox, QSpinBox, QLabel, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush
from database import DatabaseService
from lang.local_translator import LocalTranslator
from crud_buttons import CrudButtons
from widgets import ReferenceEditor


class FieldTemplateEditDialog(QDialog):
    """Диалог редактирования шаблона поля."""
    def __init__(self, parent=None, db=None, data=None, class_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.data = data or {}
        self.class_id = class_id or self.data.get('class_id')

        self.setWindowTitle(self.translator.tr('title_edit_field_template'))
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_field_name = QLineEdit(self.data.get('field_name', ''))
        form.addRow(self.translator.tr('field_name'), self.edit_field_name)

        self.combo_type = QComboBox()
        types = self.db.execute_query("SELECT ccode, cname FROM meta.field_types ORDER BY cname")
        for ccode, cname in types:
            self.combo_type.addItem(f"{cname} ({ccode})", ccode)
        current_type = self.data.get('field_type', 'C')
        idx = self.combo_type.findData(current_type)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.combo_type.currentIndexChanged.connect(self.on_type_changed)
        form.addRow(self.translator.tr('field_type'), self.combo_type)

        self.edit_alias = QLineEdit(self.data.get('calias', ''))
        form.addRow(self.translator.tr('field_alias'), self.edit_alias)

        self.spin_length = QSpinBox()
        self.spin_length.setRange(1, 10000)
        self.spin_length.setValue(self.data.get('nlength', 255))
        form.addRow(self.translator.tr('field_length'), self.spin_length)

        self.chk_indexed = QCheckBox(self.translator.tr('field_index'))
        self.chk_indexed.setChecked(self.data.get('is_indexed', True))
        form.addRow(self.chk_indexed)

        self.ref_layout = QHBoxLayout()
        self.combo_ref_type = QComboBox()
        self.combo_ref_type.addItem(self.translator.tr('ref_none'), None)
        self.combo_ref_type.addItem(self.translator.tr('ref_entity'), "entity")
        self.combo_ref_type.addItem(self.translator.tr('ref_class'), "class")
        self.combo_ref_type.currentIndexChanged.connect(self.on_ref_type_changed)
        self.ref_layout.addWidget(self.combo_ref_type)

        self.ref_entity_combo = QComboBox()
        self.ref_entity_combo.addItem("--", None)
        entities = self.db.execute_query("SELECT id, cname, calias FROM meta.entitytypes ORDER BY cname")
        for eid, cname, calias in entities:
            self.ref_entity_combo.addItem(f"{cname} ({calias})", eid)
        self.ref_layout.addWidget(self.ref_entity_combo)

        self.ref_class_combo = QComboBox()
        self.ref_class_combo.addItem("--", None)
        classes = self.db.execute_query("SELECT id, cname, calias FROM meta.entity_classes ORDER BY cname")
        for cid, cname, calias in classes:
            self.ref_class_combo.addItem(f"{cname} ({calias})", cid)
        self.ref_layout.addWidget(self.ref_class_combo)

        form.addRow(self.translator.tr('field_ref_type'), self.ref_layout)

        self.spin_order = QSpinBox()
        self.spin_order.setRange(0, 10000)
        self.spin_order.setValue(self.data.get('sort_order', 10))
        form.addRow(self.translator.tr('field_order'), self.spin_order)

        layout.addLayout(form)
        self.restore_ref_values()

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.on_type_changed()

    def restore_ref_values(self):
        ref_entity_id = self.data.get('ref_entitytype_id')
        ref_class_id = self.data.get('ref_class_id')
        if ref_entity_id:
            self.combo_ref_type.setCurrentIndex(self.combo_ref_type.findData("entity"))
            idx = self.ref_entity_combo.findData(ref_entity_id)
            if idx >= 0:
                self.ref_entity_combo.setCurrentIndex(idx)
        elif ref_class_id:
            self.combo_ref_type.setCurrentIndex(self.combo_ref_type.findData("class"))
            idx = self.ref_class_combo.findData(ref_class_id)
            if idx >= 0:
                self.ref_class_combo.setCurrentIndex(idx)
        else:
            self.combo_ref_type.setCurrentIndex(self.combo_ref_type.findData(None))

    def on_type_changed(self):
        is_ref = self.combo_type.currentData() == 'R'
        self.combo_ref_type.setEnabled(is_ref)
        self.ref_entity_combo.setEnabled(is_ref and self.combo_ref_type.currentData() == "entity")
        self.ref_class_combo.setEnabled(is_ref and self.combo_ref_type.currentData() == "class")
        self.spin_length.setEnabled(not is_ref)

    def on_ref_type_changed(self):
        ref_type = self.combo_ref_type.currentData()
        self.ref_entity_combo.setEnabled(ref_type == "entity")
        self.ref_class_combo.setEnabled(ref_type == "class")

    def get_data(self):
        ref_type = self.combo_ref_type.currentData()
        ref_entity_id = None
        ref_class_id = None
        if ref_type == "entity":
            ref_entity_id = self.ref_entity_combo.currentData()
        elif ref_type == "class":
            ref_class_id = self.ref_class_combo.currentData()

        return {
            'field_name': self.edit_field_name.text().strip(),
            'field_type': self.combo_type.currentData(),
            'calias': self.edit_alias.text().strip(),
            'nlength': self.spin_length.value(),
            'is_indexed': self.chk_indexed.isChecked(),
            'ref_entitytype_id': ref_entity_id,
            'ref_class_id': ref_class_id,
            'sort_order': self.spin_order.value(),
            'class_id': self.class_id
        }


class CompositionTemplateEditDialog(QDialog):
    """Диалог добавления/редактирования шаблона дочерней таблицы."""
    def __init__(self, parent=None, db=None, data=None, class_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.data = data or {}
        self.class_id = class_id or self.data.get('class_id')

        self.setWindowTitle(self.translator.tr('title_edit_composition_template'))
        self.resize(500, 300)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.ref_child = ReferenceEditor(
            table_name='meta.entitytypes',
            display_field='cname',
            db=self.db
        )
        if self.data.get('child_entitytype_id'):
            child_id = self.data['child_entitytype_id']
            res = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id = %s", (child_id,))
            if res:
                self.ref_child.set_value(child_id, res[0][0])
        form.addRow(self.translator.tr('field_child_entity'), self.ref_child)

        self.combo_role = QComboBox()
        roles = self.db.execute_query("SELECT id, cname, calias FROM meta.composition_roles ORDER BY cname")
        for rid, rname, ralias in roles:
            self.combo_role.addItem(f"{rname} ({ralias})", rid)
        if self.data.get('role_id'):
            idx = self.combo_role.findData(self.data['role_id'])
            if idx >= 0:
                self.combo_role.setCurrentIndex(idx)
        form.addRow(self.translator.tr('field_role'), self.combo_role)

        self.edit_link_field = QLineEdit(self.data.get('c_link_fieldname', ''))
        form.addRow(self.translator.tr('field_link_field'), self.edit_link_field)

        self.spin_order = QSpinBox()
        self.spin_order.setRange(0, 10000)
        self.spin_order.setValue(self.data.get('isortorder', 10))
        form.addRow(self.translator.tr('field_order'), self.spin_order)

        self.chk_required = QCheckBox(self.translator.tr('field_required'))
        self.chk_required.setChecked(self.data.get('is_required', True))
        form.addRow(self.chk_required)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_data(self):
        return {
            'child_entitytype_id': self.ref_child.get_value(),
            'role_id': self.combo_role.currentData(),
            'c_link_fieldname': self.edit_link_field.text().strip(),
            'isortorder': self.spin_order.value(),
            'is_required': self.chk_required.isChecked(),
            'class_id': self.class_id
        }


class ClassTemplatesTab(QWidget):
    """Вкладка шаблонов классов: поля + дочерние таблицы."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.current_class_id = None

        layout = QVBoxLayout(self)

        # Верхняя панель: выбор класса
        top_layout = QHBoxLayout()
        self.lbl_class = QLabel(self.translator.tr('class_label'))
        top_layout.addWidget(self.lbl_class)
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_changed)
        top_layout.addWidget(self.class_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # ВЕРХНЯЯ ЧАСТЬ: Шаблоны полей
        self.lbl_fields = QLabel("<b>" + self.translator.tr('field_templates') + "</b>")
        layout.addWidget(self.lbl_fields)

        self.fields_table = QTableWidget(0, 8)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.fields_table)

        self.fields_crud = CrudButtons(self)
        layout.addWidget(self.fields_crud)
        self.fields_crud.add_clicked.connect(self.add_field_template)
        self.fields_crud.edit_clicked.connect(self.edit_field_template)
        self.fields_crud.delete_clicked.connect(self.delete_field_template)

        # Разделитель
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        # НИЖНЯЯ ЧАСТЬ: Шаблоны дочерних таблиц
        self.lbl_comp = QLabel("<b>" + self.translator.tr('composition_templates') + "</b>")
        layout.addWidget(self.lbl_comp)

        self.comp_table = QTableWidget(0, 6)
        self.comp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.comp_table.setColumnHidden(5, True)
        layout.addWidget(self.comp_table)

        self.comp_crud = CrudButtons(self)
        layout.addWidget(self.comp_crud)
        self.comp_crud.add_clicked.connect(self.add_composition_template)
        self.comp_crud.edit_clicked.connect(self.edit_composition_template)
        self.comp_crud.delete_clicked.connect(self.delete_composition_template)

        self.load_classes()
        self.retranslate_ui()

    def retranslate_ui(self):
        # Заголовок "Класс:"
        if hasattr(self, 'lbl_class'):
            self.lbl_class.setText(self.translator.tr('class_label'))

        # Заголовки секций
        if hasattr(self, 'lbl_fields'):
            self.lbl_fields.setText("<b>" + self.translator.tr('field_templates') + "</b>")
        if hasattr(self, 'lbl_comp'):
            self.lbl_comp.setText("<b>" + self.translator.tr('composition_templates') + "</b>")

        # Заголовки таблиц
        self.fields_table.setHorizontalHeaderLabels([
            self.translator.tr('field_name'),
            self.translator.tr('field_type'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_length'),
            self.translator.tr('field_index'),
            self.translator.tr('field_ref_type'),
            self.translator.tr('field_ref_target'),
            self.translator.tr('field_order')
        ])
        self.fields_table.horizontalHeader().setStretchLastSection(True)

        self.comp_table.setHorizontalHeaderLabels([
            self.translator.tr('field_child_entity'),
            self.translator.tr('field_role'),
            self.translator.tr('field_link_field'),
            self.translator.tr('field_order'),
            self.translator.tr('field_required'),
            ''
        ])
        self.comp_table.horizontalHeader().setStretchLastSection(True)

        # Кнопки CRUD
        if hasattr(self, 'fields_crud'):
            self.fields_crud.retranslate_ui()
        if hasattr(self, 'comp_crud'):
            self.comp_crud.retranslate_ui()

    def load_classes(self):
        self.class_combo.clear()
        rows = self.db.execute_query(
            "SELECT id, cname, calias FROM meta.entity_classes ORDER BY cname"
        )
        for cid, cname, calias in rows:
            self.class_combo.addItem(f"{cname} ({calias})", cid)

    def on_class_changed(self, index):
        if index >= 0:
            self.current_class_id = self.class_combo.currentData()
            self.load_field_templates()
            self.load_composition_templates()

    # ========================================================================
    # ШАБЛОНЫ ПОЛЕЙ
    # ========================================================================

    def load_field_templates(self):
        if not self.current_class_id:
            self.fields_table.setRowCount(0)
            return
        sql = """
            SELECT id, field_name, field_type, calias, nlength, is_indexed,
                   ref_entitytype_id, ref_class_id, sort_order
            FROM meta.class_field_templates
            WHERE class_id = %s
            ORDER BY sort_order
        """
        rows = self.db.execute_query(sql, (self.current_class_id,))
        self.fields_table.setRowCount(0)
        for row in rows:
            fid, fname, ftype, calias, length, indexed, ref_entity_id, ref_class_id, order = row
            r = self.fields_table.rowCount()
            self.fields_table.insertRow(r)
            self.fields_table.setItem(r, 0, QTableWidgetItem(fname))
            self.fields_table.setItem(r, 1, QTableWidgetItem(ftype))
            self.fields_table.setItem(r, 2, QTableWidgetItem(calias or ""))
            self.fields_table.setItem(r, 3, QTableWidgetItem(str(length) if length else ""))
            self.fields_table.setItem(r, 4, QTableWidgetItem(
                self.translator.tr('yes') if indexed else self.translator.tr('no')))

            if ref_entity_id:
                self.fields_table.setItem(r, 5, QTableWidgetItem(self.translator.tr('ref_entity')))
                ref_name = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (ref_entity_id,))
                self.fields_table.setItem(r, 6, QTableWidgetItem(ref_name[0][0] if ref_name else str(ref_entity_id)))
            elif ref_class_id:
                self.fields_table.setItem(r, 5, QTableWidgetItem(self.translator.tr('ref_class')))
                class_name = self.db.execute_query("SELECT cname FROM meta.entity_classes WHERE id=%s", (ref_class_id,))
                self.fields_table.setItem(r, 6, QTableWidgetItem(class_name[0][0] if class_name else str(ref_class_id)))
            else:
                self.fields_table.setItem(r, 5, QTableWidgetItem(""))
                self.fields_table.setItem(r, 6, QTableWidgetItem(""))

            self.fields_table.setItem(r, 7, QTableWidgetItem(str(order)))
            self.fields_table.item(r, 0).setData(Qt.UserRole, fid)

    def add_field_template(self):
        if not self.current_class_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_class_first'))
            return
        dlg = FieldTemplateEditDialog(self, db=self.db, class_id=self.current_class_id)
        if dlg.exec_():
            data = dlg.get_data()
            try:
                self.db.execute_query("""
                    INSERT INTO meta.class_field_templates
                        (class_id, field_name, field_type, calias, nlength, is_indexed, 
                         ref_entitytype_id, ref_class_id, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (data['class_id'], data['field_name'], data['field_type'],
                      data['calias'], data['nlength'], data['is_indexed'],
                      data['ref_entitytype_id'], data['ref_class_id'], data['sort_order']), fetch=False)
                self.load_field_templates()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def edit_field_template(self):
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_template_first'))
            return
        template_id = self.fields_table.item(current_row, 0).data(Qt.UserRole)
        row = self.db.execute_query(
            """SELECT field_name, field_type, calias, nlength, is_indexed, 
                      ref_entitytype_id, ref_class_id, sort_order
               FROM meta.class_field_templates WHERE id = %s""",
            (template_id,)
        )
        if not row:
            return
        data = {
            'field_name': row[0][0], 'field_type': row[0][1], 'calias': row[0][2],
            'nlength': row[0][3], 'is_indexed': row[0][4],
            'ref_entitytype_id': row[0][5], 'ref_class_id': row[0][6],
            'sort_order': row[0][7], 'class_id': self.current_class_id
        }
        dlg = FieldTemplateEditDialog(self, db=self.db, data=data, class_id=self.current_class_id)
        if dlg.exec_():
            new_data = dlg.get_data()
            try:
                self.db.execute_query("""
                    UPDATE meta.class_field_templates SET
                        field_name=%s, field_type=%s, calias=%s, nlength=%s,
                        is_indexed=%s, ref_entitytype_id=%s, ref_class_id=%s, sort_order=%s
                    WHERE id=%s
                """, (new_data['field_name'], new_data['field_type'], new_data['calias'],
                      new_data['nlength'], new_data['is_indexed'], new_data['ref_entitytype_id'],
                      new_data['ref_class_id'], new_data['sort_order'], template_id), fetch=False)
                self.load_field_templates()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def delete_field_template(self):
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_template_first'))
            return
        template_id = self.fields_table.item(current_row, 0).data(Qt.UserRole)
        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_template')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM meta.class_field_templates WHERE id=%s", (template_id,), fetch=False)
            self.load_field_templates()

    # ========================================================================
    # ШАБЛОНЫ ДОЧЕРНИХ ТАБЛИЦ
    # ========================================================================

    def load_composition_templates(self):
        if not self.current_class_id:
            self.comp_table.setRowCount(0)
            return
        sql = """
            SELECT cct.id, et.cname AS child_name, cr.cname AS role_name,
                   cct.c_link_fieldname, cct.isortorder, cct.is_required,
                   cr.calias AS role_calias
            FROM meta.class_composition_templates cct
            JOIN meta.entitytypes et ON cct.child_entitytype_id = et.id
            JOIN meta.composition_roles cr ON cct.role_id = cr.id
            WHERE cct.class_id = %s
            ORDER BY cct.isortorder
        """
        rows = self.db.execute_query(sql, (self.current_class_id,))
        self.comp_table.setRowCount(0)
        for row in rows:
            tid, child_name, role_name, link_field, order, required, role_calias = row
            r = self.comp_table.rowCount()
            self.comp_table.insertRow(r)
            self.comp_table.setItem(r, 0, QTableWidgetItem(child_name))
            self.comp_table.setItem(r, 1, QTableWidgetItem(role_name))
            self.comp_table.setItem(r, 2, QTableWidgetItem(link_field))
            self.comp_table.setItem(r, 3, QTableWidgetItem(str(order)))
            self.comp_table.setItem(r, 4, QTableWidgetItem(
                self.translator.tr('yes') if required else self.translator.tr('no')))

            item_id = QTableWidgetItem(str(tid))
            item_id.setData(Qt.UserRole, tid)
            item_id.setData(Qt.UserRole + 1, role_calias)
            self.comp_table.setItem(r, 5, item_id)

            is_system_role = role_calias in ('FILES',)
            if is_system_role or required:
                for col in range(5):
                    it = self.comp_table.item(r, col)
                    if it:
                        it.setForeground(QBrush(Qt.darkCyan))

    def add_composition_template(self):
        if not self.current_class_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_class_first'))
            return
        dlg = CompositionTemplateEditDialog(self, db=self.db, class_id=self.current_class_id)
        if dlg.exec_():
            data = dlg.get_data()
            if not data['child_entitytype_id']:
                QMessageBox.warning(self, self.translator.tr('warning'), "Выберите дочернюю сущность")
                return
            try:
                self.db.execute_query("""
                    INSERT INTO meta.class_composition_templates
                        (class_id, child_entitytype_id, role_id, c_link_fieldname, isortorder, is_required)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (data['class_id'], data['child_entitytype_id'], data['role_id'],
                      data['c_link_fieldname'], data['isortorder'], data['is_required']), fetch=False)
                self.load_composition_templates()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def edit_composition_template(self):
        current_row = self.comp_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_template_first'))
            return

        item_id = self.comp_table.item(current_row, 5)
        template_id = item_id.data(Qt.UserRole)
        role_calias = item_id.data(Qt.UserRole + 1)

        if role_calias in ('FILES',):
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Системные шаблоны нельзя редактировать")
            return

        row = self.db.execute_query(
            """SELECT child_entitytype_id, role_id, c_link_fieldname, isortorder, is_required
               FROM meta.class_composition_templates WHERE id = %s""",
            (template_id,)
        )
        if not row:
            return
        data = {
            'child_entitytype_id': row[0][0], 'role_id': row[0][1],
            'c_link_fieldname': row[0][2], 'isortorder': row[0][3],
            'is_required': row[0][4], 'class_id': self.current_class_id
        }
        dlg = CompositionTemplateEditDialog(self, db=self.db, data=data, class_id=self.current_class_id)
        if dlg.exec_():
            new_data = dlg.get_data()
            try:
                self.db.execute_query("""
                    UPDATE meta.class_composition_templates SET
                        child_entitytype_id=%s, role_id=%s, c_link_fieldname=%s,
                        isortorder=%s, is_required=%s
                    WHERE id=%s
                """, (new_data['child_entitytype_id'], new_data['role_id'],
                      new_data['c_link_fieldname'], new_data['isortorder'],
                      new_data['is_required'], template_id), fetch=False)
                self.load_composition_templates()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def delete_composition_template(self):
        current_row = self.comp_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_template_first'))
            return

        item_id = self.comp_table.item(current_row, 5)
        template_id = item_id.data(Qt.UserRole)
        role_calias = item_id.data(Qt.UserRole + 1)

        if role_calias in ('FILES',):
            QMessageBox.warning(self, self.translator.tr('warning'),
                                "Системные шаблоны нельзя удалить")
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_template')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM meta.class_composition_templates WHERE id=%s", (template_id,), fetch=False)
            self.load_composition_templates()