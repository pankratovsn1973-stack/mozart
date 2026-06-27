# widgets/form_designer_old/property_loader.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget


class ControlPropertyLoader:
    """Сервис вычитки и локализации ERP-свойств для таблицы инспектора."""

    TRANSLATIONS = {
        "label": "Текст надписи (Label)",
        "binding_field": "Биндинг поля (Физическая колонка)",
        "entity_alias": "Биндинг к справочнику (Entity Alias)",
        "display_field": "Отображаемое поле справочника",
        "selector_form": "ID формы выбора (Selector Form)",
        "is_required": "Обязательное поле",
        "is_readonly": "Только для чтения",
        "objectName": "Имя объекта в коде"
    }

    @classmethod
    def load_form_properties(cls, table_widget, form_obj):
        """Заполняет таблицу свойствами бланка формы."""
        pos = form_obj.pos()
        properties = [
            ("Имя формы (Alias)", "form_alias", getattr(form_obj, 'form_alias', 'Новая форма'), "str", False),
            ("Заголовок окна", "title", getattr(form_obj, 'title', 'Форма'), "str", False),
            ("Координата X (Left)", "x", int(pos.x()), "int", False),
            ("Координата Y (Top)", "y", int(pos.y()), "int", False),
            ("Ширина формы", "width", int(form_obj.width), "int", False),
            ("Высота формы", "height", int(form_obj.height), "int", False),
        ]
        for label, prop_name, value, val_type, readonly in properties:
            table_widget.add_property_row(label, prop_name, value, val_type, readonly)

    @classmethod
    def load_control_properties(cls, table_widget, proxy_item):
        """Динамически сканирует и выводит расширенные ERP-параметры контрола."""
        # 1. Сбор геометрии в зависимости от того, прокси перед нами или голый виджет
        if hasattr(proxy_item, "rect") and hasattr(proxy_item, "pos"):
            rect, pos = proxy_item.rect(), proxy_item.pos()
            width, height = int(rect.width()), int(rect.height())
            x, y = int(pos.x()), int(pos.y())
            control_id = getattr(proxy_item, 'control_id', '')
            control_type = getattr(proxy_item, 'control_type', 'textbox')
        else:
            # Если это внутренний под-контрол рантайма (например, QLineEdit)
            width, height = int(proxy_item.width()), int(proxy_item.height())
            x, y = int(proxy_item.x()), int(proxy_item.y())
            control_id = proxy_item.objectName() or "child"
            control_type = proxy_item.__class__.__name__

        base_props = [
            ("ID Контрола", "control_id", control_id, "str", True),
            ("Тип поля", "control_type", control_type, "str", True),
            ("Координата X (Left)", "x", x, "int", False),
            ("Координата Y (Top)", "y", y, "int", False),
            ("Ширина (Width)", "width", width, "int", False),
            ("Высота (Height)", "height", height, "int", False),
        ]

        for label, prop_name, value, val_type, readonly in base_props:
            table_widget.add_property_row(label, prop_name, value, val_type, readonly)

        # 2. Безопасное определение целевого виджета для глубокого инспектирования свойств
        if hasattr(proxy_item, 'widget') and callable(proxy_item.widget):
            inner_widget = proxy_item.widget()
        else:
            inner_widget = proxy_item

        if inner_widget:
            from .property_inspector import PropertyInspector
            dynamic_props = PropertyInspector.inspect(inner_widget)

            for tech_name, (default_display, val, val_type) in dynamic_props.items():
                if tech_name in ("x", "y", "width", "height", "control_id", "control_type"):
                    continue
                display_name = cls.TRANSLATIONS.get(tech_name, default_display)
                table_widget.add_property_row(display_name, tech_name, val, val_type, readonly=False)
