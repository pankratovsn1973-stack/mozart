# /home/sergey/Documents/configurate/tabs/forms_tab.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QMessageBox, QDialog
)
from PySide6.QtCore import Qt

from database import DatabaseService
from lang.local_translator import LocalTranslator
from .forms import FormPropertiesDialog
from .forms.form_wizard import FormWizard


class FormsTab(QWidget):
    """Вкладка управления формами"""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton(self.translator.tr('btn_add'))
        self.btn_add.clicked.connect(self.add_form)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton(self.translator.tr('btn_edit'))
        self.btn_edit.clicked.connect(self.edit_form)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete.clicked.connect(self.delete_form)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Дерево форм
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_entity')
        ])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 150)
        self.tree.itemDoubleClicked.connect(self.edit_form)
        layout.addWidget(self.tree)

        self.retranslate_ui()
        self.load_forms()

    def retranslate_ui(self):
        """Обновление переводов"""
        self.btn_add.setText(self.translator.tr('btn_add'))
        self.btn_edit.setText(self.translator.tr('btn_edit'))
        self.btn_delete.setText(self.translator.tr('btn_delete'))
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_name'),
            self.translator.tr('field_alias'),
            self.translator.tr('field_entity')
        ])

    def load_forms(self):
        """Загружает список форм из БД"""
        sql = """
            SELECT f.id, f.cname, f.calias, f.ientitytypeid, et.cname as entity_name
            FROM meta.forms f
            LEFT JOIN meta.entitytypes et ON f.ientitytypeid = et.id
            ORDER BY f.cname
        """
        rows = self.db.execute_query(sql)
        self.tree.clear()

        for row in rows:
            item = QTreeWidgetItem()
            item.setText(0, str(row[0]))
            item.setText(1, row[1] or "")
            item.setText(2, row[2] or "")
            item.setText(3, row[4] or "")
            item.setData(0, Qt.UserRole, row[0])
            self.tree.addTopLevelItem(item)

    def get_selected_id(self):
        """Возвращает ID выбранной формы"""
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def add_form(self):
        """Добавление новой формы"""
        # Спрашиваем, хочет ли пользователь использовать мастер
        reply = QMessageBox.question(
            self,
            self.translator.tr('question'),
            self.translator.tr('use_form_wizard'),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            # Открываем мастер
            wizard = FormWizard(self.db, parent=self)
            if wizard.exec_() == QDialog.Accepted:
                result = wizard.get_result()
                self._create_form_from_wizard(result)
        else:
            # Старый способ — пустая форма
            dlg = FormPropertiesDialog(None, db=self.db)
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                self._save_form(data)

    def edit_form(self):
        """Редактирование формы"""
        form_id = self.get_selected_id()
        if not form_id:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_select_form')
            )
            return

        sql = """
            SELECT cname, calias, ientitytypeid, mstate_json 
            FROM meta.forms WHERE id = %s
        """
        row = self.db.execute_query(sql, (form_id,))
        if not row:
            return

        data = {
            "cname": row[0][0],
            "calias": row[0][1],
            "ientitytypeid": row[0][2],
            "mstate_json": row[0][3]
        }

        # parent=None для независимости от DBWorkDialog
        dlg = FormPropertiesDialog(None, data, db=self.db, form_id=form_id)
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()
            self._save_form(new_data, form_id)

    def delete_form(self):
        """Удаление формы"""
        form_id = self.get_selected_id()
        if not form_id:
            return

        # Проверяем, есть ли элементы у формы
        res = self.db.execute_query(
            "SELECT COUNT(*) FROM meta.form_elements WHERE formid = %s",
            (form_id,)
        )
        count = res[0][0] if res else 0

        msg = self.translator.tr('confirm_delete_form')
        if count > 0:
            msg += f"\n\n{self.translator.tr('warning_form_has_elements')}: {count}"

        reply = QMessageBox.question(
            self,
            self.translator.tr('confirm_delete'),
            msg,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM meta.form_elements WHERE formid = %s",
                (form_id,),
                fetch=False
            )
            self.db.execute_query(
                "DELETE FROM meta.forms WHERE id = %s",
                (form_id,),
                fetch=False
            )
            self.load_forms()

    def _save_form(self, data, form_id=None):
        """Сохраняет форму в БД"""
        mstate = data.get("mstate_json")
        if isinstance(mstate, dict):
            mstate = json.dumps(mstate, ensure_ascii=False)

        if form_id:
            sql = """
                UPDATE meta.forms 
                SET cname=%s, calias=%s, ientitytypeid=%s, mstate_json=%s
                WHERE id=%s
            """
            self.db.execute_query(sql, (
                data["cname"], data["calias"],
                data["ientitytypeid"], mstate, form_id
            ), fetch=False)
        else:
            sql = """
                INSERT INTO meta.forms (cname, calias, ientitytypeid, mstate_json)
                VALUES (%s, %s, %s, %s) RETURNING id
            """
            res = self.db.execute_query(sql, (
                data["cname"], data["calias"], data["ientitytypeid"], mstate
            ))
            if res:
                form_id = res[0][0]

        self.load_forms()
        return form_id

    def _create_form_from_wizard(self, result):
        """Создаёт форму по результатам мастера"""
        # Генерируем JSON формы на основе выбранных полей
        form_json = self._generate_form_json(result)

        form_id = self._save_form({
            'cname': result['form_name'],
            'calias': result['form_alias'],
            'ientitytypeid': result['entity_id'],
            'mstate_json': form_json
        })

        if form_id:
            QMessageBox.information(
                self,
                self.translator.tr('info'),
                self.translator.tr('form_created_success')
            )

    def _generate_form_json(self, result):
        """Генерирует JSON формы на основе выбранных полей"""
        if result['is_grid']:
            return self._generate_grid_form_json(result)
        else:
            return self._generate_edit_form_json(result)

    def _generate_grid_form_json(self, result):
        """Генерирует JSON для табличной формы"""
        columns = []
        for field in result['selected_fields']:
            # Получаем информацию о поле
            field_info = self.db.execute_query(
                """
                SELECT calias, cfieldtype 
                FROM meta.fields 
                WHERE cfieldname = %s AND entitytypeid = %s
                """,
                (field, result['entity_id'])
            )
            if field_info:
                columns.append({
                    "field": field,
                    "header": field_info[0][0],
                    "width": 150
                })

        return {
            "class": "MozartForm",
            "objectName": result['form_alias'],
            "windowTitle": result['form_name'],
            "geometry": {"x": 0, "y": 0, "width": 1000, "height": 600},
            "widgets": [
                {
                    "class": "MozartGrid",
                    "name": "grid_main",
                    "geometry": {"x": 10, "y": 10, "width": 980, "height": 500},
                    "properties": {
                        "columns_json": json.dumps(columns),
                        "allow_filter": True,
                        "allow_sort": True
                    }
                }
            ],
            "toolbar": [
                {"text": self.translator.tr('btn_add'), "action": "add", "icon": "add"},
                {"text": self.translator.tr('btn_edit'), "action": "edit", "icon": "edit"},
                {"text": self.translator.tr('btn_delete'), "action": "delete", "icon": "delete"}
            ],
            "custom_properties": {
                "entity_alias": result.get('entity_alias', ''),
                "form_type": "grid"
            }
        }

    def _generate_edit_form_json(self, result):
        """Генерирует JSON для формы редактирования"""
        controls = []
        y = 10

        # Получаем класс контрола по типу поля
        def get_control_type(field_type):
            type_map = {
                'C': 'TextBox',
                'I': 'NumberBox',
                'N': 'NumberBox',
                'D': 'DateBox',
                'T': 'DateBox',
                'L': 'CheckBox',
                'M': 'Memo',
                'R': 'Reference'
            }
            return type_map.get(field_type, 'TextBox')

        for field in result['selected_fields']:
            field_info = self.db.execute_query(
                """
                SELECT calias, cfieldtype 
                FROM meta.fields 
                WHERE cfieldname = %s AND entitytypeid = %s
                """,
                (field, result['entity_id'])
            )
            if field_info:
                calias = field_info[0][0]
                field_type = field_info[0][1]
                control_type = get_control_type(field_type)

                control = {
                    "class": f"Mozart{control_type}",
                    "name": field,
                    "geometry": {"x": 10, "y": y, "width": 300, "height": 30},
                    "properties": {
                        "label": calias,
                        "binding_field": field
                    }
                }

                # Для ссылочных полей добавляем entity_alias
                if field_type == 'R':
                    # Получаем целевую сущность для ссылки
                    ref_res = self.db.execute_query(
                        """
                        SELECT ref_entitytypeid 
                        FROM meta.fields 
                        WHERE cfieldname = %s AND entitytypeid = %s
                        """,
                        (field, result['entity_id'])
                    )
                    if ref_res and ref_res[0][0]:
                        ref_entity = self.db.execute_query(
                            "SELECT calias FROM meta.entitytypes WHERE id = %s",
                            (ref_res[0][0],)
                        )
                        if ref_entity:
                            control["properties"]["entity_alias"] = ref_entity[0][0]
                            control["properties"]["display_field"] = "cname"

                controls.append(control)
                y += 40

        # Вычисляем высоту формы
        height = min(800, y + 100)

        return {
            "class": "MozartForm",
            "objectName": result['form_alias'],
            "windowTitle": result['form_name'],
            "geometry": {"x": 0, "y": 0, "width": 600, "height": height},
            "widgets": controls,
            "toolbar": [
                {"text": self.translator.tr('btn_save'), "action": "save", "icon": "save"},
                {"text": self.translator.tr('btn_cancel'), "action": "cancel", "icon": "cancel"}
            ],
            "custom_properties": {
                "entity_alias": result.get('entity_alias', ''),
                "form_type": "edit"
            }
        }