# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_objects_registry.py

import uuid


class FormObjectsRegistry:
    """Глобальный реестр визуальных объектов на холсте дизайнера."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FormObjectsRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._registry = {}
        return cls._instance

    def register_object(self, widget_obj, parent_container_id=None, explicit_id=None):
        """Регистрирует объект в памяти, отсекая системные фоновые подложки Qt."""
        if not widget_obj:
            return "form_root"

        # ЖЕСТКИЙ СИСТЕМНЫЙ БАРЬЕР: Запрещаем регистрировать фоновую подложку холста и заголовки
        class_name = widget_obj.__class__.__name__
        if class_name in ("FormBackground", "QLabel"):
            obj_name = getattr(widget_obj, "objectName", lambda: "")()
            if obj_name not in ("lbl_of_ref", "txt_of_ref"):
                if class_name == "FormBackground" or (
                        widget_obj.parent() and widget_obj.parent().__class__.__name__ == "FormBackground"):
                    return "form_root"

        # Проверяем, не зарегистрирован ли объект ранее
        for obj_ptr, meta in self._registry.items():
            if meta["widget_ref"] == widget_obj:
                if explicit_id and meta["control_id"] != str(explicit_id):
                    meta["control_id"] = str(explicit_id)
                return meta["control_id"]

        control_id = str(explicit_id) if explicit_id else str(uuid.uuid4())[:8]

        if hasattr(widget_obj, 'objectName') and widget_obj.objectName():
            alias = widget_obj.objectName()
        elif hasattr(widget_obj, 'form_alias') and widget_obj.form_alias:
            alias = widget_obj.form_alias
        else:
            alias = f"control_{control_id}"

        self._registry[id(widget_obj)] = {
            "control_id": control_id,
            "parent_id": parent_container_id if parent_container_id else None,
            "object_name": alias,
            "widget_ref": widget_obj
        }
        return control_id

    def get_id_by_widget(self, widget_obj):
        """Интеллектуальный поиск ID с распознаванием пар прокси-виджет."""
        if not widget_obj:
            return "form_root"

        if widget_obj.__class__.__name__ == "FormBackground":
            return "form_root"

        if id(widget_obj) in self._registry:
            return self._registry[id(widget_obj)]["control_id"]

        for obj_ptr, meta in self._registry.items():
            ref = meta.get("widget_ref")
            if hasattr(ref, 'widget') and callable(ref.widget) and ref.widget() == widget_obj:
                return meta["control_id"]
            if hasattr(widget_obj, 'widget') and callable(widget_obj.widget) and widget_obj.widget() == ref:
                return meta["control_id"]

        return "unknown"

    def get_widget_by_id(self, control_id):
        """Возвращает инстанс объекта по его строковому ID."""
        cid_str = str(control_id).strip()
        if cid_str in ("0", "form_root"):
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.allWidgets():
                if widget.__class__.__name__ == "FormDesigner" and hasattr(widget, 'runtime_form'):
                    return widget.runtime_form

        for obj_ptr, meta in self._registry.items():
            if meta["control_id"] == cid_str:
                return meta["widget_ref"]
        return None

    def clear(self):
        """Полная зачистка реестра."""
        self._registry.clear()

    def clear_registry(self):
        self.clear()
