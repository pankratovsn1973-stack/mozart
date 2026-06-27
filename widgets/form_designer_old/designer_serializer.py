# widgets/form_designer_old/designer_serializer.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt
from .designer_data_model import DesignerDataModel


class DesignerSerializer:
    """Изолированный парсер для сборки данных формы в один атомарный JSON-пакет для СУБД."""

    @staticmethod
    def update_debug_grid(table_widget, control_id: str):
        """Отрисовка среза сырой In-Memory СУБД в нижнюю таблицу."""
        if not table_widget:
            return

        table_widget.setRowCount(0)
        model = DesignerDataModel()

        row_idx = 0
        for (map_cid, prop_name), val_str in model.properties_instances.items():
            if map_cid == control_id:
                table_widget.insertRow(row_idx)

                id_item = QTableWidgetItem(str(map_cid))
                id_item.setForeground(Qt.GlobalColor.darkGray)
                table_widget.setItem(row_idx, 0, id_item)

                name_item = QTableWidgetItem(str(prop_name))
                table_widget.setItem(row_idx, 1, name_item)

                val_item = QTableWidgetItem(str(val_str))
                if (map_cid, prop_name) in model.properties_delta:
                    val_item.setForeground(Qt.GlobalColor.blue)
                    val_item.setText(f"{val_str} (Δ: {model.properties_delta[(map_cid, prop_name)]})")

                table_widget.setItem(row_idx, 2, val_item)
                row_idx += 1

    @staticmethod
    def pack_form_payload(runtime_form, raw_mstate_str: str, scene_obj) -> dict:
        """Собирает монолитный слепок, включая саму форму под ID=0 в общий массив элементов."""
        controls = []
        if scene_obj and hasattr(scene_obj, 'get_controls_data'):
            controls = scene_obj.get_controls_data()

        model = DesignerDataModel()
        model.commit_delta()

        # 1. Извлекаем физическую геометрию самого бланка формы с экрана
        if runtime_form:
            current_width = int(runtime_form.width)
            current_height = int(runtime_form.height)
            current_x = int(runtime_form.pos().x())
            current_y = int(runtime_form.pos().y())
        else:
            try:
                current_width = int(float(model.get_value("form_root", "width") or 800))
                current_height = int(float(model.get_value("form_root", "height") or 600))
                current_x = int(float(model.get_value("form_root", "x") or 0))
                current_y = int(float(model.get_value("form_root", "y") or 0))
            except:
                current_width, current_height = 800, 600
                current_x, current_y = 0, 0

        # 2. ПЕРЕПИСЫВАЕМ МЕХАНИЗМ: Добавляем саму форму как полноценный элемент под ID = '0' в начало списка
        form_properties = {
            "x": current_x,
            "y": current_y,
            "width": current_width,
            "height": current_height,
            "form_alias": model.get_value("form_root", "form_alias") or "OrdinaryDictionary",
            "title": model.get_value("form_root", "title") or "СтандСправочник"
        }

        form_element_record = {
            "id": "0",  # Жесткий эталонный ID для формы как элемента
            "parentid": None,  # У формы нет родителя верхнего уровня
            "calias": form_properties["form_alias"],
            "cclass": "form",  # Класс объекта — форма
            "properties": form_properties  # Все свойства упакованы в стандартный паспорт
        }

        # Вставляем запись формы самой первой строкой в итоговую выгрузку элементов холста
        controls.insert(0, form_element_record)

        # 3. Сохраняем обратную совместимость для mstate_json (на всякий случай, если внешние скрипты еще читают forms)
        updated_mstate = {}
        if raw_mstate_str:
            try:
                clean_str = raw_mstate_str.strip("[]'\"")
                updated_mstate = json.loads(clean_str)
            except:
                pass

        if "geometry" not in updated_mstate:
            updated_mstate["geometry"] = {}

        updated_mstate["geometry"]["width"] = current_width
        updated_mstate["geometry"]["height"] = current_height
        updated_mstate["geometry"]["x"] = current_x
        updated_mstate["geometry"]["y"] = current_y
        updated_mstate["windowTitle"] = form_properties["title"]
        updated_mstate["class"] = "MozartForm"

        # Возвращаем монолитный структурированный пакет
        return {
            "width": current_width,
            "height": current_height,
            "x": current_x,
            "y": current_y,
            "title": form_properties["title"],
            "form_alias": form_properties["form_alias"],
            "mstate_json": json.dumps(updated_mstate, ensure_ascii=False),
            "controls": controls  # В этом массиве теперь лежит и сама форма под ID=0, и все референсы
        }
