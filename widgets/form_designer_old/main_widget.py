# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/main_widget.py

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
    """Главный виджет WYSIWYG-дизайнера форм Mozart ERP."""

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

        # ИСПРАВЛЕНО: Задаем начальные пропорции вертикального разделения правой панели
        right_panel_splitter.setSizes([450, 250])
        splitter.addWidget(right_panel_splitter)

        # ИСПРАВЛЕНО: Задаем начальные пропорции горизонтального сплиттера: Палитра | Холст | Свойства
        splitter.setSizes([180, 700, 350])
        main_layout.addWidget(splitter)

        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.geometry_changed.connect(self._on_geometry_changed)

    def init_form(self, width, height, title):
        if self.property_panel:
            self.property_panel.block_sync = True

        self.runtime_form = self.scene.init_form(width, height, title)

        if self.db and self.form_id:
            try:
                res = self.db.execute_query("SELECT mstate_json FROM meta.forms WHERE id = %s", (self.form_id,))
                if res:
                    self._raw_mstate_json = str(res)
            except Exception as e:
                pass

        explicit_fid = "form_root"
        FormObjectsRegistry().register_object(self.runtime_form, explicit_id=explicit_fid)

        model = DesignerDataModel()
        model.properties_instances[(explicit_fid, "width")] = str(int(width))
        model.properties_instances[(explicit_fid, "height")] = str(int(height))
        model.properties_instances[(explicit_fid, "x")] = "0"
        model.properties_instances[(explicit_fid, "y")] = "0"
        model.properties_instances[(explicit_fid, "title")] = str(title)
        model.properties_instances[(explicit_fid, "form_alias")] = "OrdinaryDictionary"

        if self.view:
            self.view.resetCachedContent()
        self.scene.invalidate(self.scene.sceneRect(), QGraphicsScene.SceneLayer.BackgroundLayer)
        self.scene.update()

        self.property_panel.set_form(self)
        self.property_panel.block_sync = False
        self.property_panel._reload_properties_from_model()

        DesignerSerializer.update_debug_grid(self.db_debug_table, explicit_fid)
        return self.runtime_form

    def get_form_data(self) -> dict:
        return DesignerSerializer.pack_form_payload(self.runtime_form, self._raw_mstate_json, self.scene)

    def _on_control_selected(self, control_item):
        if control_item is None:
            self.property_panel.set_form(self)
            DesignerSerializer.update_debug_grid(self.db_debug_table, "form_root")
        else:
            self.property_panel.set_control(control_item)
            cid = str(getattr(self.property_panel, 'current_control_id', 'form_root')).strip()
            DesignerSerializer.update_debug_grid(self.db_debug_table, cid)

    def _on_geometry_changed(self, control_id, x, y, width, height):
        """Слот фиксации измененной геометрии с жестким разделением контекстов."""
        cid_str = str(control_id).strip()
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        is_form = (cid_str in ("0", "form_root"))
        if self.runtime_form and cid_str == registry.get_id_by_widget(self.runtime_form):
            is_form = True

        if is_form:
            target_id = "form_root"
            model.set_value(target_id, "width", str(int(width)))
            model.set_value(target_id, "height", str(int(height)))
            cid_str = "form_root"
        else:
            model.set_value(cid_str, "x", str(int(x)))
            model.set_value(cid_str, "y", str(int(y)))
            model.set_value(cid_str, "width", str(int(width)))
            model.set_value(cid_str, "height", str(int(height)))

        if self.property_panel:
            self.property_panel.update_geometry_values(x, y, width, height, sender_id=cid_str)

        DesignerSerializer.update_debug_grid(self.db_debug_table, cid_str)
