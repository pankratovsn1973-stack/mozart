# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_controls_mixin.py

from PySide6.QtCore import Qt, QPointF
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class ControlsMixin:
    """Миксин: добавление, удаление, выделение контролов, сохранение данных."""

    def _init_controls(self):
        self.controls = {}
        self.selected_control = None
        # ❌ УДАЛЕНО: self.control_handles больше не нужен

    def add_control(self, control_widget, control_id, control_type, x, y, parent_item=None, calias="", full_path=""):
        from .control_item import ControlItem

        try:
            x, y = float(x or 50.0), float(y or 50.0)
        except (ValueError, TypeError):
            x, y = 50.0, 50.0

        actual_parent = parent_item if parent_item else self.background
        item = ControlItem(control_widget, control_id, control_type, parent=actual_parent)
        item.setPos(QPointF(x, y))

        parent_container_id = str(parent_item.control_id) if (
                parent_item and hasattr(parent_item, 'control_id')) else None
        FormObjectsRegistry().register_object(
            item,
            parent_container_id=parent_container_id,
            explicit_id=str(control_id),
            calias=calias,
            full_path=full_path
        )

        item.selected_changed.connect(lambda sel: self._on_control_selected(item, sel))
        item.geometry_changed.connect(self._on_control_geometry_changed)

        self.controls[control_id] = item
        if hasattr(control_widget, 'set_design_mode'):
            control_widget.set_design_mode(True)

        if hasattr(self, 'control_added'):
            self.control_added.emit(item)
        return item

    def _on_control_selected(self, control_item, selected):
        """✅ ИСПРАВЛЕНО: Передача управления фокусом в централизованный метод сцены."""
        if selected and control_item:
            self.selected_control = control_item
            # Вместо создания маркеров здесь — передаем фокус
            if hasattr(self, 'set_focused_control'):
                self.set_focused_control(control_item)
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(control_item)
        else:
            if len(self.selectedItems()) == 0:
                self.selected_control = None
                if hasattr(self, 'set_focused_control'):
                    self.set_focused_control(None)
                if hasattr(self, 'control_selected'):
                    self.control_selected.emit(None)

    def _on_control_geometry_changed(self, control_id, x, y, width, height):
        if hasattr(self, 'geometry_changed'):
            self.geometry_changed.emit(str(control_id), int(x), int(y), int(width), int(height))

    def get_controls_data(self) -> list:
        controls_list = []
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        system_garbage_classes = ('formbackground', 'resizehandle', 'formbackgroundsignals')
        system_garbage_ids = ('form_root', '1')

        form_db_id = "841"
        if hasattr(self, 'background') and self.background:
            form_db_id = registry.get_id_by_widget(self.background)
            if form_db_id == "unknown":
                form_db_id = "841"

        processed_children = set()

        for obj_ptr, metadata in list(registry._registry.items()):
            widget_ref = metadata["widget_ref"]
            control_id = str(metadata["control_id"]).strip()
            parent_id = metadata["parent_id"]
            calias = metadata["object_name"]

            if hasattr(widget_ref, 'isVisible') and not widget_ref.isVisible():
                continue
            if hasattr(widget_ref, 'widget') and hasattr(widget_ref.widget(),
                                                         'isVisible') and not widget_ref.widget().isVisible():
                continue

            raw_class = str(getattr(widget_ref, 'control_type', widget_ref.__class__.__name__)).lower()

            is_deleted = False
            if hasattr(widget_ref, 'scene') and widget_ref.scene() is None:
                is_deleted = True
            elif hasattr(widget_ref, 'graphicsProxyWidget'):
                proxy = widget_ref.graphicsProxyWidget()
                if not proxy or proxy.scene() is None:
                    is_deleted = True

            if is_deleted or raw_class in system_garbage_classes or control_id in system_garbage_ids or calias in (
                    "control_1", "control_840"):
                continue

            if raw_class in ('qlineedit', 'qpushbutton', 'qlabel') and not parent_id:
                continue

            cclass = model.get_value(control_id, "control_type")
            if not cclass:
                cclass = raw_class
                if cclass == "qlabel":
                    cclass = "textbox"

            props = {}
            if hasattr(widget_ref, 'properties') and isinstance(widget_ref.properties, dict):
                props.update(widget_ref.properties)

            if hasattr(widget_ref, 'rect') and hasattr(widget_ref, 'pos'):
                pos, rect = widget_ref.pos(), widget_ref.rect()
                props['x'], props['y'] = int(pos.x()), int(pos.y())
                props['width'], props['height'] = int(rect.width()), int(rect.height())
            elif hasattr(widget_ref, 'geometry'):
                geo = widget_ref.geometry()
                parent_widget = widget_ref.parentWidget()
                parent_proxy = parent_widget.graphicsProxyWidget() if parent_widget else None
                offset_x = int(parent_proxy.pos().x()) if parent_proxy else 0
                offset_y = int(parent_proxy.pos().y()) if parent_proxy else 0
                props['x'], props['y'] = geo.x() + offset_x, geo.y() + offset_y
                props['width'], props['height'] = geo.width(), geo.height()

            resolved_parent = str(parent_id) if parent_id else str(form_db_id)

            controls_list.append({
                'id': control_id,
                'parentid': resolved_parent,
                'calias': calias,
                'cclass': str(cclass).lower(),
                'properties': props
            })

            actual_widget = getattr(widget_ref, 'widget', lambda: None)() if hasattr(widget_ref,
                                                                                     'widget') else widget_ref
            if actual_widget and hasattr(actual_widget, 'findChildren'):
                from PySide6.QtWidgets import QWidget
                for child in actual_widget.findChildren(QWidget):
                    if not child.isVisible():
                        continue
                    if id(child) in processed_children:
                        continue

                    child_name = getattr(child, 'name', child.objectName())
                    if child_name and child_name in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref',
                                                     'lbl_of_ref'):
                        processed_children.add(id(child))

                        child_id = registry.get_id_by_widget(child)

                        if child_id == "unknown":
                            for k_instances in list(model.properties_instances.keys()):
                                k_cid = k_instances
                                if model.get_value(k_cid, "form_alias") == child_name:
                                    for o_ptr, m_reg in list(registry._registry.items()):
                                        if str(m_reg["control_id"]).strip() == control_id:
                                            child_id = k_cid
                                            registry.register_object(child, parent_container_id=control_id,
                                                                     explicit_id=child_id)
                                            break

                        if child_id == "unknown":
                            child_id = str(uuid.uuid4())[:8]
                            registry.register_object(child, parent_container_id=control_id, explicit_id=child_id)

                        erp_class = model.get_value(child_id, "control_type")
                        if not erp_class:
                            if child_name == 'txt_of_ref':
                                erp_class = 'textbox'
                            else:
                                child_class = child.__class__.__name__
                                if child_class == 'QPushButton' or 'btn' in child_name:
                                    erp_class = 'button'
                                elif child_class == 'QLabel' or 'lbl' in child_name:
                                    erp_class = 'label'
                                else:
                                    erp_class = 'textbox'

                        child_geo = child.geometry()
                        props_child = {
                            'x': int(child_geo.x()),
                            'y': int(child_geo.y()),
                            'width': int(child_geo.width()),
                            'height': int(child_geo.height())
                        }
                        if hasattr(child, 'properties') and isinstance(child.properties, dict):
                            props_child.update(child.properties)

                        controls_list.append({
                            'id': child_id,
                            'parentid': control_id,
                            'calias': str(child_name),
                            'cclass': str(erp_class).lower(),
                            'properties': props_child
                        })

        return controls_list