# tabs/forms_wizard_factory.py
# -*- coding: utf-8 -*-

import json


class FormsWizardFactory:
    """Изолированная фабрика для сборки плоских JSON-структур low-code мастера."""

    @staticmethod
    def generate_grid_json(result, db_service) -> dict:
        """Генерирует плоский low-code JSON для табличной формы."""
        columns = []
        for field in result['selected_fields']:
            field_info = db_service.execute_query(
                "SELECT calias FROM meta.fields WHERE cfieldname = %s AND entitytypeid = %s",
                (field, result['entity_id'])
            )
            if field_info and isinstance(field_info, list) and len(field_info) > 0:
                header_text = str(field_info[0][0])
            else:
                header_text = str(field)

            columns.append({"field": str(field), "header": header_text, "width": 150})

        return {
            "class": "MozartForm",
            "objectName": str(result['form_alias']),
            "windowTitle": str(result['form_name']),
            "entity_alias": str(result.get('entity_alias', '')),
            "form_type": "grid",
            "geometry": {"x": 0, "y": 0, "width": 1000, "height": 600},
            "controls": [{
                "id": "1",
                "parentid": None,
                "calias": f"table_{result['form_alias']}",
                "cclass": "table",
                "properties": {
                    "x": 10, "y": 50, "width": 980, "height": 500,
                    "columns_json": json.dumps(columns, ensure_ascii=False)
                }
            }]
        }

    @staticmethod
    def generate_edit_json(result, db_service) -> dict:
        """Генерирует плоский low-code JSON для карточки редактирования поля."""
        controls = []
        y_cursor = 50

        def get_control_type(field_type):
            type_map = {'C': 'textbox', 'I': 'numberbox', 'N': 'numberbox', 'D': 'datebox',
                        'T': 'datebox', 'L': 'checkbox', 'M': 'memo', 'R': 'reference'}
            return type_map.get(str(field_type).upper(), 'textbox')

        for idx, field in enumerate(result['selected_fields']):
            field_info = db_service.execute_query(
                "SELECT calias, cfieldtype FROM meta.fields WHERE cfieldname = %s AND entitytypeid = %s",
                (field, result['entity_id'])
            )
            if field_info and isinstance(field_info, list) and len(field_info) > 0:
                calias = str(field_info[0][0])
                field_type = str(field_info[0][1])
            else:
                calias, field_type = str(field), 'C'

            cclass_type = get_control_type(field_type)
            control_properties = {
                "x": 20, "y": y_cursor,
                "width": 400 if cclass_type in ('reference', 'memo') else 250,
                "height": 70 if cclass_type == 'memo' else 32,
                "label": calias, "binding_field": str(field),
                "is_required": False, "is_readonly": False
            }

            if field_type == 'R':
                ref_res = db_service.execute_query(
                    "SELECT ref_entitytypeid FROM meta.fields WHERE cfieldname = %s AND entitytypeid = %s",
                    (field, result['entity_id'])
                )
                if ref_res and isinstance(ref_res, list) and len(ref_res) > 0 and ref_res[0][0]:
                    ref_id = ref_res[0][0]
                    ref_entity = db_service.execute_query("SELECT calias FROM meta.entitytypes WHERE id = %s", (ref_id,))
                    if ref_entity and isinstance(ref_entity, list) and len(ref_entity) > 0:
                        control_properties["entity_alias"] = str(ref_entity[0][0])
                        control_properties["display_field"] = "cname"

            controls.append({
                "id": str(100 + idx),
                "parentid": None,
                "calias": f"{cclass_type}_{field}",
                "cclass": cclass_type,
                "properties": control_properties
            })
            y_cursor += (control_properties["height"] + 12)

        final_height = min(1200, max(600, y_cursor + 60))
        return {
            "class": "MozartForm",
            "objectName": str(result['form_alias']),
            "windowTitle": str(result['form_name']),
            "entity_alias": str(result.get('entity_alias', '')),
            "form_type": "edit",
            "geometry": {"x": 0, "y": 0, "width": 600, "height": final_height},
            "controls": controls
        }
