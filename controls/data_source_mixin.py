# controls/data_source_mixin.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtCore import Property


class DataSourceMixin:
    """Миксин для контролов со списками (ComboBox, ListBox, OptionGroup)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_type = "static"
        self._entity_alias = ""
        self._display_field = "cname"
        self._value_field = "id"
        self._items_json = "[]"
        self._filter_expression = ""
        self._order_by = ""
        self._query = ""
        self._db = None
        self._items_cache = []
        self._design_mode = False

    @Property(str)
    def source_type(self):
        return self._source_type

    @source_type.setter
    def source_type(self, value):
        if value in ("static", "entity", "query"):
            self._source_type = value
            if not getattr(self, '_design_mode', False):
                self.load_items()

    @Property(str)
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value
        if getattr(self, '_source_type', '') == "entity" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def display_field(self):
        return self._display_field

    @display_field.setter
    def display_field(self, value):
        self._display_field = value
        if getattr(self, '_source_type', '') == "entity" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def value_field(self):
        return self._value_field

    @value_field.setter
    def value_field(self, value):
        self._value_field = value
        if getattr(self, '_source_type', '') == "entity" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def items_json(self):
        return self._items_json

    @items_json.setter
    def items_json(self, value):
        self._items_json = value
        if getattr(self, '_source_type', '') == "static" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def filter_expression(self):
        return self._filter_expression

    @filter_expression.setter
    def filter_expression(self, value):
        self._filter_expression = value
        if getattr(self, '_source_type', '') == "entity" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def order_by(self):
        return self._order_by

    @order_by.setter
    def order_by(self, value):
        self._order_by = value
        if getattr(self, '_source_type', '') == "entity" and not getattr(self, '_design_mode', False):
            self.load_items()

    @Property(str)
    def query(self):
        return self._query

    @query.setter
    def query(self, value):
        self._query = value
        if getattr(self, '_source_type', '') == "query" and not getattr(self, '_design_mode', False):
            self.load_items()

    def set_design_mode(self, design_mode):
        self._design_mode = design_mode
        if not design_mode:
            self.load_items()

    def set_db(self, db):
        self._db = db

    def load_items(self):
        if getattr(self, '_design_mode', False):
            return
        if self._source_type == "static":
            self._load_from_static()
        elif self._source_type == "entity":
            self._load_from_entity()
        elif self._source_type == "query":
            self._load_from_query()
        else:
            self._items_cache = []
        self._update_control()

        if hasattr(self, 'items_loaded'):
            self.items_loaded.emit()

    def _load_from_static(self):
        try:
            items = json.loads(self._items_json)
            if isinstance(items, list):
                self._items_cache = []
                for item in items:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        value = item.get("value")
                        self._items_cache.append({"text": text, "value": value})
                    elif isinstance(item, (str, int, float)):
                        self._items_cache.append({"text": str(item), "value": item})
            else:
                self._items_cache = []
        except json.JSONDecodeError:
            self._items_cache = []

    def _load_from_entity(self):
        if not self._db or not self._entity_alias:
            self._items_cache = []
            return
        res = self._db.execute_query(
            "SELECT cname FROM meta.entitytypes WHERE calias = %s",
            (self._entity_alias,)
        )
        if not res:
            self._items_cache = []
            return
        cname = res
        ext_table = f"ext.ext_{cname}"
        sql = f"""
            SELECT e.{self._value_field}, e.{self._display_field}
            FROM {ext_table} e
            JOIN data.entity_versions v ON e.versionid = v.id
            WHERE v.cversionstatus = 'Active'
        """
        if self._filter_expression:
            sql += f" AND ({self._filter_expression})"
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        else:
            sql += f" ORDER BY e.{self._display_field}"
        rows = self._db.execute_query(sql)
        self._items_cache = [{"text": row, "value": row} for row in rows]

    def _load_from_query(self):
        if not self._db or not self._query:
            self._items_cache = []
            return
        rows = self._db.execute_query(self._query)
        self._items_cache = [{"text": row, "value": row} for row in rows]

    def _update_control(self):
        """Безопасная заглушка. Если метод переопределен в дочернем классе - выполнится он."""
        # КРИТИЧЕСКИЙ ФИКС: Убрано принудительное падение raise NotImplementedError,
        # так как при инициализации свойств в дизайнере дочерний метод может быть еще не доступен.
        pass

    def get_items(self):
        return self._items_cache

    def find_value_by_text(self, text):
        for item in self._items_cache:
            if item["text"] == text:
                return item["value"]
        return None

    def find_text_by_value(self, value):
        for item in self._items_cache:
            if item["value"] == value:
                return item["text"]
        return ""
