# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/property_helpers.py

def safe_get_width(obj):
    """Безопасно получает ширину объекта (работает и с числом, и с методом)."""
    if obj is None:
        return 0
    if hasattr(obj, 'width'):
        if callable(obj.width):
            try:
                return obj.width()
            except:
                return 0
        else:
            return obj.width
    return 0


def safe_get_height(obj):
    """Безопасно получает высоту объекта (работает и с числом, и с методом)."""
    if obj is None:
        return 0
    if hasattr(obj, 'height'):
        if callable(obj.height):
            try:
                return obj.height()
            except:
                return 0
        else:
            return obj.height
    return 0


class PropertyRow:
    def __init__(self, display_name, value, prop_type="str", internal_name=""):
        self.display_name = display_name
        self.value = value
        self.prop_type = prop_type
        self.internal_name = internal_name