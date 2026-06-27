# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/designer_data_model.py

class DesignerDataModel:
    """Локальная In-Memory СУБД для изоляции оригинальных ERP-классов от графических масок."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DesignerDataModel, cls).__new__(cls, *args, **kwargs)
            cls._instance.properties_instances = {}
            cls._instance.properties_delta = {}
            cls._instance._init_metadata()
        return cls._instance

    def _init_metadata(self):
        """Реестр метаданных low-code свойств форм и контролов ERP."""
        self.metadata = {
            "control_id": {"label": "Идентификатор ID", "type": "str"},
            "control_type": {"label": "Класс контрола", "type": "str"},
            "form_alias": {"label": "Алиас контрола", "type": "str"},
            "title": {"label": "Заголовок окна", "type": "str"},
            "x": {"label": "Параметр X", "type": "int"},
            "y": {"label": "Параметр Y", "type": "int"},
            "width": {"label": "Параметр WIDTH", "type": "int"},
            "height": {"label": "Параметр HEIGHT", "type": "int"},
            "label": {"label": "Текст надписи", "type": "str"},
            "binding_field": {"label": "Поле СУБД привязки", "type": "str"},
            "entity_alias": {"label": "Сущность-источник", "type": "str"},
            "display_field": {"label": "Отображаемое поле", "type": "str"},
            "selector_form": {"label": "Форма выбора", "type": "str"},
            "is_required": {"label": "Обязательное", "type": "bool"},
            "is_readonly": {"label": "Только чтение", "type": "bool"}
        }

    def get_metadata(self, prop_name):
        return self.metadata.get(prop_name, {"label": str(prop_name), "type": "str"})

    def set_value(self, control_id, prop_name, value, is_delta=False):
        cid = str(control_id).strip()
        if is_delta:
            self.properties_delta[(cid, prop_name)] = str(value)
        else:
            self.properties_instances[(cid, prop_name)] = str(value)

    def get_value(self, control_id, prop_name):
        cid = str(control_id).strip()
        if (cid, prop_name) in self.properties_delta:
            return self.properties_delta[(cid, prop_name)]
        return self.properties_instances.get((cid, prop_name), "")

    def commit_delta(self):
        """ВОССТАНОВЛЕНО: Перенос измененных в буфере свойств в основную память СУБД."""
        for (cid, prop_name), val in self.properties_delta.items():
            self.properties_instances[(cid, prop_name)] = val
        self.properties_delta.clear()

    def clear(self):
        self.properties_instances.clear()
        self.properties_delta.clear()
