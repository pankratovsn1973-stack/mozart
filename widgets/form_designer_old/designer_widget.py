# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/designer_widget.py

import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QApplication, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

from database import DatabaseService
from lang.local_translator import LocalTranslator
from .palette_widget import PaletteWidget
from .hierarchy_widget import HierarchyWidget
from .property_editor import PropertyEditor
from .form_scene import FormDesignerScene
from .form_view import FormDesignerView


class FormDesigner(QWidget):
    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.form_id = form_id
        self._form_properties = {
            "width": 800, "height": 600, "title": "Новая форма",
            "background_color": "#f0f0f0", "resizable": True,
            "form_type": "edit", "interface_role": ""
        }
        self._init_ui()
        if form_id:
            self.set_form_id(form_id)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Панель инструментов
        toolbar = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_form)
        toolbar.addWidget(self.btn_save)

        self.btn_load = QPushButton("Загрузить")
        self.btn_load.clicked.connect(self.load_form)
        toolbar.addWidget(self.btn_load)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_form)
        toolbar.addWidget(self.btn_clear)

        # КНОПКА СЕТКИ С ДИАГНОСТИКОЙ
        self.btn_grid = QPushButton("⊞ Сетка")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.setEnabled(True)
        self.btn_grid.clicked.connect(self._on_grid_clicked)
        toolbar.addWidget(self.btn_grid)

        # ДИАГНОСТИКА В КОНСОЛЬ
        print(f"[DESIGNER] btn_grid created: enabled={self.btn_grid.isEnabled()}, checkable={self.btn_grid.isCheckable()}, checked={self.btn_grid.isChecked()}")

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Левый сплиттер
        left_splitter = QSplitter(Qt.Vertical)
        self.palette = PaletteWidget(self)
        self.hierarchy = HierarchyWidget(self)
        left_splitter.addWidget(self.palette)
        left_splitter.addWidget(self.hierarchy)
        left_splitter.setSizes([300, 200])

        # Правая панель
        self.property_editor = PropertyEditor(self)
        self.property_editor.setMinimumWidth(10)

        # Сцена
        self.scene = FormDesignerScene(self)
        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.form_resized.connect(self._on_form_resized)
        self.view = FormDesignerView(self.scene)

        # Главный сплиттер
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(left_splitter)
        self.main_splitter.addWidget(self.view)
        self.main_splitter.addWidget(self.property_editor)
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, True)
        self.main_splitter.setCollapsible(2, True)
        self.main_splitter.setSizes([250, 600, 250])

        layout.addWidget(self.main_splitter)

        # ДИАГНОСТИКА: есть ли у сцены метод set_grid_visible?
        print(f"[DESIGNER] scene has set_grid_visible: {hasattr(self.scene, 'set_grid_visible')}")

    def _on_grid_clicked(self):
        checked = self.btn_grid.isChecked()
        print(f"[DESIGNER] grid button clicked, checked={checked}")
        if hasattr(self.scene, 'set_grid_visible'):
            self.scene.set_grid_visible(checked)
            print(f"[DESIGNER] scene.set_grid_visible({checked}) called")
        else:
            print(f"[DESIGNER] ERROR: scene has no set_grid_visible method!")

    def _on_control_selected(self, control_item):
        if control_item:
            self.property_editor.set_control(control_item)
            if hasattr(self.hierarchy, 'select_item_by_id'):
                self.hierarchy.select_item_by_id(control_item.control_id)
        else:
            self.property_editor.set_form(self)
            if hasattr(self.hierarchy, 'clear_selection'):
                self.hierarchy.clear_selection()

    def _on_form_resized(self, width, height):
        self._form_properties["width"] = width
        self._form_properties["height"] = height

    def retranslate_ui(self):
        self.btn_save.setText(self.translator.tr('btn_save') or "Сохранить")
        self.btn_load.setText(self.translator.tr('btn_load') or "Загрузить")
        self.btn_clear.setText(self.translator.tr('btn_clear') or "Очистить")

    def set_form_id(self, form_id):
        self.form_id = form_id
        self.load_form()

    def load_form(self):
        if not self.form_id or not self.db:
            return

        row = self.db.execute_query(
            "SELECT mstate_json FROM meta.forms WHERE id = %s", (self.form_id,)
        )
        if row and row[0] and row[0][0]:
            try:
                state = json.loads(row[0][0])
                if isinstance(state, dict):
                    self._form_properties.update(state.get('form', {}))
                    self.scene.init_form(
                        self._form_properties.get('width', 800),
                        self._form_properties.get('height', 600)
                    )
            except:
                pass

        rows = self.db.execute_query(
            """SELECT id, calias, cclass, cdatasource, mproperties_json
               FROM meta.form_elements WHERE formid = %s
               ORDER BY parentid NULLS FIRST, isortorder, id""",
            (self.form_id,)
        ) or []

        controls_data = []
        for r in rows:
            eid, calias, cclass, datasource, props_json = r
            props = {}
            if props_json:
                try:
                    props = json.loads(props_json)
                except:
                    pass
            controls_data.append({
                "id": str(eid), "calias": calias, "cclass": cclass,
                "parent_id": props.pop('parent_id', None),
                "x": props.pop('x', 50), "y": props.pop('y', 50),
                "width": props.pop('width', 150), "height": props.pop('height', 30),
                "properties": props
            })

        if hasattr(self.scene, 'load_controls'):
            self.scene.load_controls(controls_data)
        if hasattr(self.hierarchy, 'load_controls'):
            self.hierarchy.load_controls(controls_data)

    def save_form(self):
        if not self.form_id or not self.db:
            return

        form_state = {"form": self._form_properties}
        self.db.execute_query(
            "UPDATE meta.forms SET mstate_json = %s WHERE id = %s",
            (json.dumps(form_state, ensure_ascii=False), self.form_id), fetch=False
        )
        self.db.execute_query("DELETE FROM meta.form_elements WHERE formid = %s", (self.form_id,), fetch=False)

        controls_data = self.scene.get_controls_data() if hasattr(self.scene, 'get_controls_data') else []
        for data in controls_data:
            props = data.get('properties', {})
            props['x'] = data.get('x', 50)
            props['y'] = data.get('y', 50)
            props['width'] = data.get('width', 150)
            props['height'] = data.get('height', 30)
            self.db.execute_query(
                """INSERT INTO meta.form_elements
                   (formid, calias, cclass, cdatasource, mproperties_json)
                   VALUES (%s, %s, %s, %s, %s)""",
                (self.form_id, data['calias'], data['cclass'], '', json.dumps(props, ensure_ascii=False)),
                fetch=False
            )

    def clear_form(self):
        if hasattr(self.scene, 'clear_controls'):
            self.scene.clear_controls()
        if hasattr(self.hierarchy, 'clear'):
            self.hierarchy.clear()

    def on_property_changed(self, prop_name, value):
        selected = getattr(self.scene, 'selected_control', None)
        if not selected:
            if prop_name in self._form_properties:
                self._form_properties[prop_name] = value
            if prop_name in ("width", "height") and hasattr(self.scene, 'set_form_size'):
                self.scene.set_form_size(self._form_properties["width"], self._form_properties["height"])
            elif prop_name == "title" and hasattr(self.scene, 'set_form_title'):
                self.scene.set_form_title(str(value))
            if prop_name == "form_type" and self.scene.background:
                self.scene.background.form_type = value
                self.scene.background.update_layout()
            if prop_name == "interface_role" and self.scene.background:
                self.scene.background.interface_role = value
                self.scene.background.update_layout()
        else:
            if hasattr(self.scene, 'update_control_property'):
                self.scene.update_control_property(selected.control_id, prop_name, value)