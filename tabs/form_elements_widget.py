# /home/sergey/Documents/configurate/tabs/form_elements_widget.py
# -*- coding: utf-8 -*-
# Виджет для управления элементами формы (контролами)

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QTextEdit, QLabel
)
from PySide6.QtCore import Qt

from database import DatabaseService
from lang.local_translator import LocalTranslator
from widgets.reference_editor import ReferenceEditor


class ElementPropertiesDialog(QDialog):
    """Диалог редактирования свойств контрола"""

    def __init__(self, parent=None, data=None, db=None, parent_controls=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.db = db or DatabaseService()
        self.data = data or {}
        self.parent_controls = parent_controls or []

        self.setWindowTitle(self.translator.tr('title_element_properties'))
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Алиас (уникальное имя контрола в пределах формы)
        self.edit_calias = QLineEdit(self.data.get("calias", ""))
        form.addRow(self.translator.tr('field_alias'), self.edit_calias)

        # Тип контрола
        self.combo_class = QComboBox()
        self.combo_class.addItem(self.translator.tr('control_panel'), 'panel')
        self.combo_class.addItem(self.translator.tr('control_textbox'), 'textbox')
        self.combo_class.addItem(self.translator.tr('control_numberbox'), 'numberbox')
        self.combo_class.addItem(self.translator.tr('control_datebox'), 'datebox')
        self.combo_class.addItem(self.translator.tr('control_checkbox'), 'checkbox')
        self.combo_class.addItem(self.translator.tr('control_memo'), 'memo')
        self.combo_class.addItem(self.translator.tr('control_reference'), 'reference')
        self.combo_class.addItem(self.translator.tr('control_grid'), 'grid')
        self.combo_class.addItem(self.translator.tr('control_button'), 'button')
        self.combo_class.addItem(self.translator.tr('control_label'), 'label')
        self.combo_class.addItem(self.translator.tr('control_group'), 'group')
        self.combo_class.addItem(self.translator.tr('control_tab'), 'tab')

        current_class = self.data.get("cclass", "textbox")
        idx = self.combo_class.findData(current_class)
        if idx >= 0:
            self.combo_class.setCurrentIndex(idx)
        form.addRow(self.translator.tr('field_control_type'), self.combo_class)

        # Родительский контрол (для иерархии)
        self.combo_parent = QComboBox()
        self.combo_parent.addItem(self.translator.tr('no_parent'), None)
        for pc in self.parent_controls:
            self.combo_parent.addItem(f"{pc['calias']} ({pc['cclass']})", pc['id'])
        if self.data.get("parentid"):
            idx = self.combo_parent.findData(self.data["parentid"])
            if idx >= 0:
                self.combo_parent.setCurrentIndex(idx)
        form.addRow(self.translator.tr('field_parent_control'), self.combo_parent)

        # Источник данных
        self.edit_datasource = QLineEdit(self.data.get("cdatasource", ""))
        self.edit_datasource.setPlaceholderText('entity("person").item({id}).version()')
        form.addRow(self.translator.tr('field_datasource'), self.edit_datasource)

        # Порядок сортировки
        self.edit_sortorder = QLineEdit(str(self.data.get("isortorder", 10)))
        form.addRow(self.translator.tr('field_order'), self.edit_sortorder)

        # Дополнительные свойства JSON
        self.edit_properties = QTextEdit()
        props = self.data.get("mproperties_json", {})
        if isinstance(props, dict):
            props = json.dumps(props, indent=2, ensure_ascii=False)
        self.edit_properties.setPlainText(str(props))
        self.edit_properties.setMaximumHeight(200)
        form.addRow(self.translator.tr('field_properties_json'), self.edit_properties)

        layout.addLayout(form)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_data(self):
        props_text = self.edit_properties.toPlainText().strip()
        properties = {}
        if props_text:
            try:
                properties = json.loads(props_text)
            except:
                properties = props_text

        sortorder = 10
        try:
            sortorder = int(self.edit_sortorder.text())
        except:
            pass

        return {
            "calias": self.edit_calias.text().strip(),
            "cclass": self.combo_class.currentData(),
            "parentid": self.combo_parent.currentData(),
            "cdatasource": self.edit_datasource.text().strip(),
            "isortorder": sortorder,
            "mproperties_json": properties
        }


class FormElementsWidget(QWidget):
    """Виджет для управления элементами формы"""

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.form_id = form_id
        self.current_element_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_element)
        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_element)
        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_element)
        self.btn_up = QPushButton(self.translator.tr('btn_up'))
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down = QPushButton(self.translator.tr('btn_down'))
        self.btn_down.clicked.connect(self.move_down)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        layout.addLayout(btn_layout)

        # Дерево элементов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_alias'),
            self.translator.tr('field_control_type'),
            self.translator.tr('field_datasource')
        ])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 120)
        self.tree.itemDoubleClicked.connect(self.edit_element)
        layout.addWidget(self.tree)

        self.retranslate_ui()
        self.load_elements()

    def set_form_id(self, form_id):
        """Устанавливает ID формы и перезагружает элементы"""
        self.form_id = form_id
        self.load_elements()

    def retranslate_ui(self):
        self.btn_add.setText(self.translator.tr('btn_add'))
        self.btn_edit.setText(self.translator.tr('btn_edit'))
        self.btn_delete.setText(self.translator.tr('btn_delete'))
        self.btn_up.setText(self.translator.tr('btn_up'))
        self.btn_down.setText(self.translator.tr('btn_down'))
        self.tree.setHeaderLabels([
            self.translator.tr('field_alias'),
            self.translator.tr('field_control_type'),
            self.translator.tr('field_datasource')
        ])

    def get_parent_controls_list(self, exclude_id=None):
        """Возвращает список родительских контролов для выбора в диалоге"""
        if not self.form_id:
            return []

        sql = """
            SELECT id, calias, cclass 
            FROM meta.form_elements 
            WHERE formid = %s
            ORDER BY isortorder, id
        """
        rows = self.db.execute_query(sql, (self.form_id,))
        result = []
        for row in rows:
            eid, calias, cclass = row
            if exclude_id and eid == exclude_id:
                continue
            result.append({'id': eid, 'calias': calias, 'cclass': cclass})
        return result

    def load_elements(self):
        """Загружает дерево элементов формы"""
        self.tree.clear()
        self.items = {}

        if not self.form_id:
            return

        sql = """
            SELECT id, parentid, calias, cclass, cdatasource, isortorder
            FROM meta.form_elements
            WHERE formid = %s
            ORDER BY parentid NULLS FIRST, isortorder, id
        """
        rows = self.db.execute_query(sql, (self.form_id,))

        # Сначала создаём все элементы
        for row in rows:
            eid, parent_id, calias, cclass, datasource, sortorder = row
            item = QTreeWidgetItem()
            item.setText(0, calias or "")
            item.setText(1, cclass or "")
            item.setText(2, datasource or "")
            item.setData(0, Qt.UserRole, eid)
            item.setData(0, Qt.UserRole + 1, parent_id)
            item.setData(0, Qt.UserRole + 2, sortorder)
            self.items[eid] = item

        # Строим иерархию
        for eid, item in self.items.items():
            parent_id = item.data(0, Qt.UserRole + 1)
            if parent_id and parent_id in self.items:
                self.items[parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def get_selected_id(self):
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def add_element(self):
        if not self.form_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_no_form_selected'))
            return

        parent_controls = self.get_parent_controls_list()
        dlg = ElementPropertiesDialog(self, db=self.db, parent_controls=parent_controls)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()

            import json
            props = data.get("mproperties_json")
            if isinstance(props, dict):
                props = json.dumps(props, ensure_ascii=False)

            sql = """
                INSERT INTO meta.form_elements 
                (formid, parentid, calias, cclass, cdatasource, isortorder, mproperties_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(sql, (
                self.form_id,
                data["parentid"],
                data["calias"],
                data["cclass"],
                data["cdatasource"],
                data["isortorder"],
                props
            ), fetch=False)
            self.load_elements()

    def edit_element(self):
        element_id = self.get_selected_id()
        if not element_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_element'))
            return

        sql = """
            SELECT calias, cclass, parentid, cdatasource, isortorder, mproperties_json
            FROM meta.form_elements
            WHERE id = %s
        """
        row = self.db.execute_query(sql, (element_id,))
        if not row:
            return

        props = row[0][5]
        if props and isinstance(props, str):
            try:
                props = json.loads(props)
            except:
                pass

        data = {
            "calias": row[0][0],
            "cclass": row[0][1],
            "parentid": row[0][2],
            "cdatasource": row[0][3],
            "isortorder": row[0][4],
            "mproperties_json": props
        }

        parent_controls = self.get_parent_controls_list(exclude_id=element_id)
        dlg = ElementPropertiesDialog(self, data, db=self.db, parent_controls=parent_controls)
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()

            import json
            new_props = new_data.get("mproperties_json")
            if isinstance(new_props, dict):
                new_props = json.dumps(new_props, ensure_ascii=False)

            sql = """
                UPDATE meta.form_elements
                SET calias=%s, cclass=%s, parentid=%s, cdatasource=%s, 
                    isortorder=%s, mproperties_json=%s
                WHERE id=%s
            """
            self.db.execute_query(sql, (
                new_data["calias"],
                new_data["cclass"],
                new_data["parentid"],
                new_data["cdatasource"],
                new_data["isortorder"],
                new_props,
                element_id
            ), fetch=False)
            self.load_elements()

    def delete_element(self):
        element_id = self.get_selected_id()
        if not element_id:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_element'))
            return

        # Проверяем, есть ли дочерние элементы
        sql = "SELECT COUNT(*) FROM meta.form_elements WHERE parentid = %s"
        res = self.db.execute_query(sql, (element_id,))
        child_count = res[0][0] if res else 0

        if child_count > 0:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_element_has_children'))
            return

        if QMessageBox.question(self, self.translator.tr('confirm_delete'),
                                self.translator.tr('confirm_delete_element')) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM meta.form_elements WHERE id = %s", (element_id,), fetch=False)
            self.load_elements()

    def _move_item(self, delta):
        """Перемещает элемент вверх/вниз (меняет isortorder)"""
        element_id = self.get_selected_id()
        if not element_id:
            return

        # Получаем текущий элемент и его родителя
        sql = "SELECT parentid, isortorder FROM meta.form_elements WHERE id = %s"
        row = self.db.execute_query(sql, (element_id,))
        if not row:
            return
        parent_id, current_sort = row[0]

        new_sort = current_sort + delta
        if new_sort < 0:
            new_sort = 0

        # Обновляем порядок
        self.db.execute_query(
            "UPDATE meta.form_elements SET isortorder = %s WHERE id = %s",
            (new_sort, element_id), fetch=False
        )

        # Пересортировываем элементы с тем же родителем
        if parent_id:
            sql = """
                UPDATE meta.form_elements 
                SET isortorder = new_sort
                FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY isortorder) * 10 as new_sort
                    FROM meta.form_elements
                    WHERE parentid = %s
                ) AS sorted
                WHERE meta.form_elements.id = sorted.id
            """
            self.db.execute_query(sql, (parent_id,), fetch=False)
        else:
            sql = """
                UPDATE meta.form_elements 
                SET isortorder = new_sort
                FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY isortorder) * 10 as new_sort
                    FROM meta.form_elements
                    WHERE formid = %s AND parentid IS NULL
                ) AS sorted
                WHERE meta.form_elements.id = sorted.id
            """
            self.db.execute_query(sql, (self.form_id,), fetch=False)

        self.load_elements()

    def move_up(self):
        self._move_item(-10)

    def move_down(self):
        self._move_item(10)