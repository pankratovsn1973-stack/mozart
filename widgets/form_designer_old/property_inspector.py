# widgets/form_designer_old/property_inspector.py
# -*- coding: utf-8 -*-

import re
from PySide6.QtCore import QMetaObject


class PropertyInspector:
    """Изолированный сервис для глубокого сканирования всех свойств объектов Qt и Python"""

    @staticmethod
    def inspect(obj) -> dict:
        """
        Сканирует объект и возвращает словарь:
        { technical_name: (display_name, current_value, value_type) }
        """
        if not obj:
            return {}

        properties = {}

        # 1. Сканируем нативные свойства Qt (только если объект поддерживает мета-объектную систему)
        if hasattr(obj, 'metaObject'):
            meta_object = obj.metaObject()
            for i in range(meta_object.propertyCount()):
                prop = meta_object.property(i)
                name = prop.name()

                # Отсекаем тяжелые графические и внутренние служебные свойства Qt
                if name in ('accessibleName', 'accessibleDescription', 'layoutDirection',
                            'styleSheet', 'geometry', 'pos', 'size', 'is_modified',
                            'windowIcon', 'palette', 'font', 'cursor', 'locale'):
                    continue

                if prop.isReadable():
                    try:
                        val = prop.read(obj)
                        if hasattr(val, 'value'):  # Обработка перечислений Qt (Enums)
                            val = val.value()

                        # Формируем читаемое имя (placeholderText -> Placeholder text)
                        display_name = re.sub(r'([A-Z])', r' \1', name).strip().capitalize()
                        properties[name] = (display_name, val, type(val).__name__)
                    except:
                        pass

        # 2. Сканируем Python-переменные инстанса (self._binding_field, self._is_required и т.д.)
        if hasattr(obj, '__dict__'):
            for attr_name, attr_value in list(obj.__dict__.items()):
                # Ищем переменные, которые начинаются с одного подчеркивания
                if attr_name.startswith('_') and not attr_name.startswith('__'):
                    # Отсекаем внутренние служебные ссылки движка дизайнера и сигналы PySide
                    if attr_name in ('_original_value', '_is_dirty', '_design_background', '_runtime_form') or hasattr(
                            attr_value, 'emit'):
                        continue

                    # Вычищаем подчеркивание для технического имени (_binding_field -> binding_field)
                    tech_name = attr_name.lstrip('_')

                    # Формируем красивое отображаемое имя (binding_field -> Binding field)
                    display_name = tech_name.replace('_', ' ').capitalize()

                    # Определяем тип данных
                    val_type = type(attr_value).__name__
                    if isinstance(attr_value, bool):
                        val_type = 'bool'
                    elif isinstance(attr_value, int):
                        val_type = 'int'
                    elif isinstance(attr_value, float):
                        val_type = 'float'

                    properties[tech_name] = (display_name, attr_value, val_type)

        return properties
