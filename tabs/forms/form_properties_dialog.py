# /home/sergey/Documents/configurate/tabs/forms/form_properties_dialog.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QWidget, QLabel
)
from PySide6.QtCore import Qt

from lang.local_translator import LocalTranslator
from widgets import ReferenceEditor
from widgets.visual_form_editor import VisualFormEditor
from controls import create_control
from .form_utils import parse_mstate


class FormPropertiesDialog(QDialog):
    """Диалог редактирования свойств формы с визуальным дизайнером"""

    def __init__(self, parent=None, data=None, db=None, form_id=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.db = db
        self.form_id = form_id
        self.data = data or {}

        self.setWindowTitle(self.translator.tr('title_form_properties'))
        self.resize(1400, 900)

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        props_widget = self._create_properties_widget()
        layout.addWidget(props_widget)

        self.designer = VisualFormEditor(self, db=self.db, form_id=self.form_id)
        layout.addWidget(self.designer, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _create_properties_widget(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        form = QFormLayout()
        form.setSpacing(10)

        self.edit_cname = QLineEdit()
        self.edit_cname.setPlaceholderText("Наименование формы")
        form.addRow(self.translator.tr('field_name') + ":", self.edit_cname)

        self.edit_calias = QLineEdit()
        self.edit_calias.setPlaceholderText("system_alias")
        form.addRow(self.translator.tr('field_alias') + ":", self.edit_calias)

        self.ref_entity = ReferenceEditor(
            table_name='meta.entitytypes',
            display_field='cname',
            db=self.db
        )
        form.addRow(self.translator.tr('field_entity') + ":", self.ref_entity)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    def _load_data(self):
        self.edit_cname.setText(self.data.get("cname", ""))
        self.edit_calias.setText(self.data.get("calias", ""))

        if self.data.get("ientitytypeid"):
            res = self.db.execute_query(
                "SELECT cname FROM meta.entitytypes WHERE id = %s",
                (self.data["ientitytypeid"],)
            )
            if res:
                self.ref_entity.set_value(self.data["ientitytypeid"], res[0][0])

        mstate_json = parse_mstate(self.data.get("mstate_json", ""))
        if mstate_json and isinstance(mstate_json, dict):
            geom = mstate_json.get("geometry", {"width": 800, "height": 600})
            w = geom.get("width", 800)
            h = geom.get("height", 600)
            title = mstate_json.get("windowTitle", "Форма")
            self.designer.init_form(w, h, title)

            if hasattr(self.designer, 'runtime_form') and self.designer.runtime_form:
                self.designer.runtime_form.form_alias = self.data.get("calias", "")
                self.designer.runtime_form.entity_alias = mstate_json.get("entity_alias", "")

        if self.form_id:
            self._load_controls_to_designer()

    def _load_controls_to_designer(self):
        sql = """
            SELECT id, calias, cclass, mproperties_json
            FROM meta.form_elements
            WHERE formid = %s
            ORDER BY isortorder, id
        """
        rows = self.db.execute_query(sql, (self.form_id,))

        for row in rows:
            eid, calias, cclass, props_json = row
            props = json.loads(props_json) if props_json else {}

            control_widget = create_control(cclass, parent=None, db=self.db)
            if not control_widget:
                continue

            control_widget.setObjectName(calias)

            # Применяем свойства через сеттеры
            for key, value in props.items():
                if key == 'items_json':
                    # Явно вызываем сеттер items_json
                    if hasattr(control_widget, 'items_json'):
                        control_widget.items_json = value
                elif key == 'columns_json':
                    if hasattr(control_widget, 'columns_json'):
                        control_widget.columns_json = value
                elif key == 'tabs_json':
                    if hasattr(control_widget, 'tabs_json'):
                        control_widget.tabs_json = value
                elif key == 'orientation':
                    if hasattr(control_widget, 'orientation'):
                        control_widget.orientation = value
                elif key == 'spacing':
                    if hasattr(control_widget, 'spacing'):
                        control_widget.spacing = value
                elif hasattr(control_widget, key):
                    try:
                        setattr(control_widget, key, value)
                    except Exception as e:
                        print(f"Ошибка установки свойства {key}={value}: {e}")

            if hasattr(control_widget, 'apply_properties'):
                control_widget.apply_properties()

            x = props.get('x', 10)
            y = props.get('y', 50)
            width = props.get('width', 150)
            height = props.get('height', 30)
            control_widget.resize(width, height)

            self.designer.scene.add_control(control_widget, str(eid), cclass, x, y)

    def get_data(self):
        form_data = self.designer.get_form_data()

        ent_alias = ""
        if hasattr(self.designer, 'runtime_form') and self.designer.runtime_form:
            ent_alias = getattr(self.designer.runtime_form, 'entity_alias', '')
        elif hasattr(self.designer.scene, 'background') and self.designer.scene.background:
            bg = self.designer.scene.background
            if hasattr(bg, '_runtime_form') and bg._runtime_form:
                ent_alias = getattr(bg._runtime_form, 'entity_alias', '')

        mstate_json = {
            "class": "MozartForm",
            "objectName": self.edit_calias.text().strip() or "Form",
            "windowTitle": self.edit_cname.text().strip() or "Новая форма",
            "entity_alias": ent_alias,
            "geometry": {
                "x": 0, "y": 0,
                "width": form_data.get('form', {}).get('width', 800),
                "height": form_data.get('form', {}).get('height', 600)
            }
        }

        return {
            "cname": self.edit_cname.text().strip(),
            "calias": self.edit_calias.text().strip(),
            "ientitytypeid": self.ref_entity.get_value(),
            "mstate_json": mstate_json,
            "controls": form_data.get('controls', [])
        }

    def _save_controls(self, form_id, controls):
        self.db.execute_query("DELETE FROM meta.form_elements WHERE formid = %s", (form_id,), fetch=False)

        for idx, control in enumerate(controls):
            properties = control.get('properties', {})

            sql = """
                INSERT INTO meta.form_elements
                (formid, calias, cclass, mproperties_json, isortorder)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(sql, (
                form_id,
                control.get('calias', ''),
                control.get('cclass', 'textbox'),
                json.dumps(properties, ensure_ascii=False),
                idx * 10
            ), fetch=False)

    def accept(self):
        save_data = self.get_data()

        if self.form_id:
            sql = """
                UPDATE meta.forms
                SET cname = %s, calias = %s, ientitytypeid = %s, mstate_json = %s
                WHERE id = %s
            """
            self.db.execute_query(sql, (
                save_data['cname'],
                save_data['calias'],
                save_data['ientitytypeid'],
                json.dumps(save_data['mstate_json'], ensure_ascii=False),
                self.form_id
            ), fetch=False)
            form_id = self.form_id
        else:
            sql = """
                INSERT INTO meta.forms (cname, calias, ientitytypeid, mstate_json)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            res = self.db.execute_query(sql, (
                save_data['cname'],
                save_data['calias'],
                save_data['ientitytypeid'],
                json.dumps(save_data['mstate_json'], ensure_ascii=False)
            ))
            form_id = res[0][0] if res else None
            self.form_id = form_id

        if form_id and save_data.get('controls'):
            self._save_controls(form_id, save_data['controls'])

        super().accept()
