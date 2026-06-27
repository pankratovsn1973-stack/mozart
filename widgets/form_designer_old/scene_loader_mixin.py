# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_loader_mixin.py

import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class SceneLoaderMixin:
    """Миксин сцены: иерархическое авторазвертывание дерева метаданных и дизайн-маскирование по calias."""

    def load_controls(self, controls_data):
        if not controls_data:
            return

        from controls import create_control
        created_items_map = {}
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        # ПОДГОТОВИТЕЛЬНЫЙ ПРОХОД (Шаг 0): Индексируем уникальные цепочки calias
        records_by_name_and_parent = {}
        id_to_alias_map = {"form_root": "OrdinaryDictionary"}

        for data in controls_data:
            cid = str(data.get('id', '')).strip()
            calias = str(data.get('calias', '')).strip()
            if cid and calias:
                id_to_alias_map[cid] = calias

        for data in controls_data:
            cclass = str(data.get('cclass', 'textbox')).lower()
            cid = str(data.get('id', '')).strip()
            pid = str(data.get('parentid', '')).strip() if data.get('parentid') else "form_root"
            calias = str(data.get('calias', '')).strip()

            if cclass in ('formbackground', 'formbackgroundsignals') or cid in ('1', '840'):
                continue

            parent_alias = id_to_alias_map.get(pid, "form_root")
            records_by_name_and_parent[(parent_alias, calias)] = data

            if cid:
                model.set_value(cid, "control_type", cclass)
                model.set_value(cid, "form_alias", calias)
                props = data.get('properties', {})
                for p_name, p_val in props.items():
                    model.set_value(cid, p_name, str(p_val))

        # ЖЕСТКАЯ ОЧЕРЕДЬ ЗАГРУЗКИ: Сначала корневые контейнеры, затем их вложенные элементы
        parent_nodes = []
        child_nodes = []

        for data in controls_data:
            cclass = str(data.get('cclass', 'textbox')).lower()
            pid = data.get('parentid')

            if cclass == 'form':
                parent_nodes.insert(0, data)
            elif not pid or str(pid).strip() in ("", "None", "form_root"):
                parent_nodes.append(data)
            else:
                child_nodes.append(data)

        ordered_controls_data = parent_nodes + child_nodes

        # ОСНОВНОЙ ПРОХОД (Шаг 1): Физическая генерация
        for data in ordered_controls_data:
            try:
                cclass = str(data.get('cclass', 'textbox')).lower()
                control_id = str(data.get('id', ''))
                calias = str(data.get('calias', '')).strip()
                props = data.get('properties', {})

                if cclass in ('formbackground', 'formbackgroundsignals') or control_id in ('1',
                                                                                           '840') or calias == 'control_840':
                    continue

                x = int(float(props.pop('x', 50)))
                y = int(float(props.pop('y', 50)))
                width = int(float(props.pop('width', 150)))
                height = int(float(props.pop('height', 30)))

                if cclass == 'form':
                    if hasattr(self, 'background') and self.background:
                        registry.register_object(self.background, explicit_id=control_id)
                    continue

                parent_id = data.get('parentid')
                parent_item = created_items_map.get(str(parent_id)) if parent_id else None
                widget = None

                # Находим существующий подконтроль внутри родительского виджета по его calias
                if parent_item and hasattr(parent_item, 'widget') and parent_item.widget():
                    parent_widget = parent_item.widget()
                    for child in parent_widget.findChildren(QWidget):
                        child_name = str(getattr(child, 'name', child.objectName())).strip()
                        if child_name == calias or child.objectName() == calias:
                            widget = child
                            registry.register_object(child, parent_container_id=str(parent_id), explicit_id=control_id)
                            break

                # ИСПРАВЛЕНО: Если это дублирующая запись подконтроля, которая уже была сопоставлена, отсекаем ее
                if parent_item and widget and control_id in created_items_map:
                    continue

                # Если это независимый верхний контрол — строим через фабрику
                if not widget:
                    if cclass in ('textbox', 'numberbox', 'datebox', 'memo', 'list'):
                        widget = QLabel(parent=None)
                        widget.setStyleSheet("border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px;")
                        widget.setText(f"[{cclass.upper()}] {calias}")
                    elif cclass == 'combobox':
                        widget = create_control(cclass, parent=None, db=self.db)
                        if widget:
                            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                    else:
                        widget = create_control(cclass, parent=None, db=self.db)

                    if not widget:
                        continue
                    widget.setObjectName(calias)

                if hasattr(widget, 'properties'):
                    widget.properties = props

                # Маскирование составного референса в режиме конструирования
                if cclass == 'reference' or hasattr(widget, 'edit_runtime'):
                    if hasattr(widget, 'findChildren'):
                        for child in widget.findChildren(QWidget):
                            child_name = getattr(child, 'name', child.objectName())
                            if child_name and child_name in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref',
                                                             'lbl_of_ref'):

                                if (calias, child_name) not in records_by_name_and_parent:
                                    sub_id = str(uuid.uuid4())[:8]
                                    child_class = child.__class__.__name__

                                    if child_name == 'txt_of_ref':
                                        real_erp_class = 'textbox'
                                    elif child_class == 'QPushButton' or 'btn' in child_name:
                                        real_erp_class = 'button'
                                    elif child_class == 'QLabel' or 'lbl' in child_name:
                                        real_erp_class = 'label'
                                    else:
                                        real_erp_class = 'textbox'

                                    model.set_value(sub_id, "control_type", real_erp_class)
                                    model.set_value(sub_id, "form_alias", child_name)
                                    registry.register_object(child, parent_container_id=control_id, explicit_id=sub_id)

                    if hasattr(widget, 'edit_runtime') and widget.edit_runtime:
                        widget.edit_runtime.setVisible(False)
                    if hasattr(widget, 'edit_design') and widget.edit_design:
                        widget.edit_design.setVisible(True)
                        widget.edit_design.name = 'txt_of_ref'
                        widget.edit_design.setObjectName('txt_of_ref')

                try:
                    widget.setFixedSize(width, height)
                except:
                    pass

                # Передаем координаты в чистом локальном виде без вычитаний родительских позиций
                item = self.add_control(widget, control_id, cclass, x, y, parent_item=parent_item)

                if item and parent_item:
                    item.setZValue(1.0)
                    item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, True)
                    item.setFlag(item.GraphicsItemFlag.ItemIsFocusable, True)

                if item:
                    created_items_map[str(control_id)] = item
                    item.updateGeometry()

            except Exception as e:
                print(f"[SceneLoaderMixin] Ошибка каскадной загрузки контрола: {e}")

    def delete_control(self, control_id):
        """Жесткое тотальное удаление контрола из всех структур памяти."""
        cid_str = str(control_id).strip()
        if cid_str not in self.controls:
            return

        item = self.controls[cid_str]
        if self.selected_control == item:
            self.selected_control = None
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

        if item and item.scene() == self:
            self.removeItem(item)

        del self.controls[cid_str]

        for obj_ptr, meta in list(FormObjectsRegistry()._registry.items()):
            if str(meta["control_id"]).strip() == cid_str:
                del FormObjectsRegistry()._registry[obj_ptr]

        model = DesignerDataModel()
        for key in list(model.properties_instances.keys()):
            if key == cid_str:
                del model.properties_instances[key]

        if hasattr(self, 'control_deleted'):
            self.control_deleted.emit(cid_str)

    def clear_selection(self):
        self.clearSelection()
        self.selected_control = None
        if hasattr(self, 'control_selected'):
            self.control_selected.emit(None)
