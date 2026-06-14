# /home/sergey/Documents/configurate/controls/base_control.py
# -*- coding: utf-8 -*-


class BaseControl:
    """Базовый класс-примесь (миксин) для всех контролов Mozart"""

    def __init__(self, *args, **kwargs):
        # Игнорируем любые переданные аргументы (например, parent)
        self._binding_field = ""
        self._entity_alias = ""
        self._is_required = False
        self._is_readonly = False
        self._original_value = None
        self._is_dirty = False
        self._properties = {}

    @property
    def binding_field(self):
        return self._binding_field

    @binding_field.setter
    def binding_field(self, value):
        self._binding_field = value

    @property
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value

    @property
    def is_required(self):
        return self._is_required

    @is_required.setter
    def is_required(self, value):
        self._is_required = value

    @property
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        self._apply_readonly()

    def _apply_readonly(self):
        """Переопределяется в дочерних классах"""
        pass

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        """Возвращает словарь ВСЕХ свойств контрола"""
        return {
            'binding_field': self._binding_field,
            'entity_alias': self._entity_alias,
            'is_required': self._is_required,
            'is_readonly': self._is_readonly,
        }

    @properties.setter
    def properties(self, value):
        if not value:
            return
        self._binding_field = value.get('binding_field', '')
        self._entity_alias = value.get('entity_alias', '')
        self._is_required = value.get('is_required', False)
        self._is_readonly = value.get('is_readonly', False)

    def set_value(self, value):
        self._original_value = value
        self._is_dirty = False

    def get_value(self):
        return None

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        pass
