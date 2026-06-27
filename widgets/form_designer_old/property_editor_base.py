# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/property_editor_base.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem
from .property_table import PropertyTableWidget
from .designer_data_model import DesignerDataModel
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry


class PropertyEditorBase(PropertyTableWidget):
    """Базовый UI-компонент инспектора, отвечающий только за чистую отрисовку ячеек таблицы."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.current_control_id = None
        self._designer_ref = None

    def _reload_properties_from_model(self):
        """Вычитка строк инспектора из СУБД памяти с жестким обособлением пространства формы form_root."""
        self.block_sync = True
        self.clearContents()
        self.setRowCount(0)

        model = DesignerDataModel()
        cid = str(self.current_control_id).strip() if self.current_control_id else "form_root"
        registry = FormObjectsRegistry()

        is_form_focused = (cid in ("0", "form_root"))
        focused_widget = registry.get_widget_by_id(cid)
        if focused_widget and focused_widget.__class__.__name__ == "FormBackground":
            is_form_focused = True

        if is_form_focused:
            props_to_load = ["form_alias", "title", "x", "y", "width", "height"]
            cid = "form_root"
        else:
            # ИСПРАВЛЕНО: Добавлен параметр parent_alias для отображения владельца контрола в инспекторе
            props_to_load = ["control_id", "control_type", "form_alias", "parent_alias", "x", "y", "width", "height",
                             "label", "binding_field", "entity_alias", "display_field",
                             "selector_form", "is_required", "is_readonly"]

        for prop_name in props_to_load:
            meta = model.get_metadata(prop_name)
            display_label = meta["label"]
            if prop_name == "parent_alias":
                display_label = "Владелец контрола"

            readonly = True if prop_name in ("control_id", "control_type", "parent_alias") else False

            if prop_name == "control_id":
                raw_val = cid
            elif prop_name == "control_type":
                raw_val = model.get_value(cid, "control_type")
                if not raw_val:
                    if self.current_item and getattr(self.current_item, 'objectName', lambda: '')() == 'txt_of_ref':
                        raw_val = "textbox"
                    elif self.current_item and hasattr(self.current_item, 'control_type'):
                        raw_val = str(self.current_item.control_type)
                    elif self.current_item:
                        raw_val = str(self.current_item.__class__.__name__).lower()
                        if raw_val == "qlabel":
                            raw_val = "textbox"
                    else:
                        raw_val = "textbox"
            elif prop_name == "parent_alias":
                # Автоматически вычисляем алиас родительского контейнера по метаданным реестра
                raw_val = "form_root"
                for obj_ptr, meta_reg in list(registry._registry.items()):
                    if str(meta_reg["control_id"]).strip() == cid:
                        pid = meta_reg["parent_id"]
                        if pid and pid != "form_root":
                            raw_val = model.get_value(str(pid), "form_alias") or f"control_{pid}"
                        break
            else:
                raw_val = model.get_value(cid, prop_name)

            if not raw_val and is_form_focused:
                if self._designer_ref and getattr(self._designer_ref, 'runtime_form', None):
                    form_obj = self._designer_ref.runtime_form
                    if prop_name == "x":
                        raw_val = "0"
                    elif prop_name == "y":
                        raw_val = "0"
                    elif prop_name == "width":
                        raw_val = str(int(form_obj.width))
                    elif prop_name == "height":
                        raw_val = str(int(form_obj.height))
                    elif prop_name == "title":
                        raw_val = getattr(form_obj, 'title', "СтандСправочник")
                    elif prop_name == "form_alias":
                        raw_val = getattr(form_obj, 'form_alias', "OrdinaryDictionary")

            row_idx = self.rowCount()
            self.insertRow(row_idx)

            label_item = QTableWidgetItem(str(display_label))
            label_item.setData(Qt.ItemDataRole.UserRole, prop_name)
            if readonly:
                label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.setItem(row_idx, 0, label_item)

            val_item = QTableWidgetItem(str(raw_val))
            if readonly:
                val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                val_item.setBackground(Qt.GlobalColor.lightGray)
            self.setItem(row_idx, 1, val_item)

        self.block_sync = False
