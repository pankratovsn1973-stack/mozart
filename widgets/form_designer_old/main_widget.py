# /home/sergey/Documents/configurate/widgets/form_designer_old/main_widget.py
# -*- coding: utf-8 -*-

"""
Модуль: Главный виджет WYSIWYG-дизайнера форм Mozart ERP.

Роль в архитектуре Mozart ERP:
    - Основной контейнер для всех компонентов визуального дизайнера.
    - Координирует работу палитры, сцены, инспектора свойств и панелей.
    - Управляет загрузкой и сохранением форм.
    - Интегрирует все миксины и компоненты в единое целое.

Ключевые зависимости:
    - FormDesignerScene - графическая сцена.
    - PropertyEditor - инспектор свойств.
    - PaletteWidget - палитра контролов.
    - FormObjectsRegistry - реестр объектов.
    - DesignerDataModel - in-memory хранилище.
"""

import json
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGraphicsScene, QTableWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont

from .form_scene import FormDesignerScene
from .property_editor import PropertyEditor
from .palette_widget import PaletteWidget
from .toolbar_bar import ToolBarBar
from .control_item_base import ControlItemBase
from .designer_data_model import DesignerDataModel
from .designer_view import DesignerGraphicsView
from .designer_serializer import DesignerSerializer
from .form_objects_registry import FormObjectsRegistry


class FormDesigner(QWidget):

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db
        self.form_id = form_id
        self.scene = None
        self.view = None
        self.toolbar_panel = None
        self.palette_panel = None
        self.property_panel = None
        self.db_debug_table = None
        self.runtime_form = None
        self._raw_mstate_json = ""

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar_panel = ToolBarBar(self)
        self.toolbar_panel.set_db(self.db)
        main_layout.addWidget(self.toolbar_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.palette_panel = PaletteWidget(self)
        splitter.addWidget(self.palette_panel)

        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.scene = FormDesignerScene(self)
        self.scene.set_db(self.db)

        self.view = DesignerGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setDragMode(DesignerGraphicsView.DragMode.RubberBandDrag)
        self.view.setAcceptDrops(True)
        canvas_layout.addWidget(self.view)

        canvas_container.setLayout(canvas_layout)
        splitter.addWidget(canvas_container)

        right_panel_splitter = QSplitter(Qt.Orientation.Vertical)

        self.property_panel = PropertyEditor(self)
        right_panel_splitter.addWidget(self.property_panel)

        debug_container = QWidget()
        debug_layout = QVBoxLayout(debug_container)
        debug_container.setContentsMargins(0, 4, 0, 0)
        debug_layout.setSpacing(2)

        debug_label = QLabel("Сырые данные DesignerDataModel (Таблица 1):")
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        debug_label.setFont(font)
        debug_label.setStyleSheet("color: #ff5500; background-color: #ffeadd; padding: 2px;")
        debug_layout.addWidget(debug_label)

        self.db_debug_table = QTableWidget()
        self.db_debug_table.setColumnCount(3)
        self.db_debug_table.setHorizontalHeaderLabels(["ID Объекта", "Свойство", "Значение в СУБД"])
        self.db_debug_table.horizontalHeader().setStretchLastSection(True)
        self.db_debug_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        debug_layout.addWidget(self.db_debug_table)
        debug_container.setLayout(debug_layout)
        right_panel_splitter.addWidget(debug_container)

        right_panel_splitter.setSizes([450, 250])
        splitter.addWidget(right_panel_splitter)

        splitter.setSizes([180, 700, 350])
        main_layout.addWidget(splitter)

        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.geometry_changed.connect(self._on_geometry_changed)

    def init_form(self, width, height, title, form_id="841"):
        """Инициализация бланка формы с ID из БД."""
        if self.property_panel:
            self.property_panel.block_sync = True

        self.runtime_form = self.scene.init_form(width, height, title, form_id)

        if self.db and self.form_id:
            try:
                res = self.db.execute_query(
                    "SELECT mstate_json FROM meta.forms WHERE id = %s",
                    (self.form_id,)
                )
                if res:
                    self._raw_mstate_json = str(res)
            except Exception as e:
                pass

        model = DesignerDataModel()
        model.set_value(form_id, "width", str(int(width)))
        model.set_value(form_id, "height", str(int(height)))
        model.set_value(form_id, "x", "0")
        model.set_value(form_id, "y", "0")
        model.set_value(form_id, "title", str(title))
        model.set_value(form_id, "form_alias", "OrdinaryDictionary")

        if self.view:
            self.view.resetCachedContent()
        self.scene.invalidate(self.scene.sceneRect(), QGraphicsScene.SceneLayer.BackgroundLayer)
        self.scene.update()

        self.property_panel.set_form(self)
        self.property_panel.block_sync = False
        self.property_panel._reload_properties_from_model()

        DesignerSerializer.update_debug_grid(self.db_debug_table, form_id)
        return self.runtime_form

    def get_form_data(self) -> dict:
        return DesignerSerializer.pack_form_payload(
            self.runtime_form,
            self._raw_mstate_json,
            self.scene
        )

    def _on_control_selected(self, control_item):
        if control_item is None:
            self.property_panel.set_form(self)
            DesignerSerializer.update_debug_grid(self.db_debug_table, "form_root")
        else:
            self.property_panel.set_control(control_item)
            cid = str(getattr(self.property_panel, 'current_control_id', 'form_root')).strip()
            DesignerSerializer.update_debug_grid(self.db_debug_table, cid)

    def _on_geometry_changed(self, control_id, x, y, width, height):
        cid_str = str(control_id).strip()
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        is_form = (cid_str in ("0", "form_root"))
        if self.runtime_form and cid_str == registry.get_id_by_widget(self.runtime_form):
            is_form = True

        if is_form:
            target_id = "841"
            model.set_value(target_id, "width", str(int(width)))
            model.set_value(target_id, "height", str(int(height)))
            cid_str = target_id
        else:
            model.set_value(cid_str, "x", str(int(x)))
            model.set_value(cid_str, "y", str(int(y)))
            model.set_value(cid_str, "width", str(int(width)))
            model.set_value(cid_str, "height", str(int(height)))

        if self.property_panel:
            self.property_panel.update_geometry_values(x, y, width, height, sender_id=cid_str)

        DesignerSerializer.update_debug_grid(self.db_debug_table, cid_str)

    def load_form(self):
        """Загрузка формы из БД."""
        if not self.form_id or not self.db:
            return

        form_id_from_db = str(self.form_id)

        row = self.db.execute_query(
            "SELECT cname, calias, mstate_json FROM meta.forms WHERE id = %s",
            (self.form_id,)
        )

        form_alias = "OrdinaryDictionary"
        form_title = "Новая форма"
        form_width = 800
        form_height = 600

        if row and row[0]:
            form_title = row[0][0] or "Новая форма"
            form_alias = row[0][1] or "OrdinaryDictionary"

            try:
                state = json.loads(row[0][2]) if row[0][2] else {}
                if isinstance(state, dict):
                    form_width = state.get('geometry', {}).get('width', 800)
                    form_height = state.get('geometry', {}).get('height', 600)
                    form_title = state.get('windowTitle', form_title)
            except:
                pass

        self.init_form(form_width, form_height, form_title, form_id_from_db)

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
                "id": str(eid),
                "calias": calias,
                "cclass": cclass,
                "parentid": str(props.pop('parentid', None)) if props.get('parentid') else None,
                "x": props.pop('x', 50),
                "y": props.pop('y', 50),
                "width": props.pop('width', 150),
                "height": props.pop('height', 30),
                "properties": props
            })

        if hasattr(self.scene, 'load_controls'):
            self.scene.load_controls(controls_data)

    def save_form(self):
        if not self.form_id or not self.db:
            return

        form_data = self.get_form_data()

        self.db.execute_query(
            "UPDATE meta.forms SET mstate_json = %s WHERE id = %s",
            (form_data.get('mstate_json', '{}'), self.form_id),
            fetch=False
        )

        controls = form_data.get('controls', [])
        if controls:
            self.db.execute_query(
                "DELETE FROM meta.form_elements WHERE formid = %s",
                (self.form_id,),
                fetch=False
            )

            for data in controls:
                props = data.get('properties', {})
                self.db.execute_query(
                    """INSERT INTO meta.form_elements
                       (formid, calias, cclass, parentid, mproperties_json)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        self.form_id,
                        data.get('calias', ''),
                        data.get('cclass', 'textbox'),
                        data.get('parentid'),
                        json.dumps(props, ensure_ascii=False)
                    ),
                    fetch=False
                )

    def clear_form(self):
        if hasattr(self.scene, 'clear_controls'):
            self.scene.clear_controls()

    def on_property_changed(self, prop_name, value):
        selected = getattr(self.scene, 'selected_control', None)
        if not selected:
            if prop_name in ("width", "height") and hasattr(self.scene, 'set_form_size'):
                self.scene.set_form_size(self.scene.background.width, self.scene.background.height)
        else:
            if hasattr(self.scene, 'update_control_property'):
                self.scene.update_control_property(selected.control_id, prop_name, value)