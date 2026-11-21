# -*- coding: utf-8 -*-
# core/method_collection.py
"""
Коллекция методов ОДНОГО экземпляра объекта на сцене (или класса).
Пишет события в change_log при любом изменении модели.

Правила:
  - Индексация — только по ID (method.id), не по имени.
  - Новые методы получают уникальный отрицательный ID
    из CollectionManager.next_negative_id().
  - Уникальность имени в пределах родителя (одной коллекции).
  - Все мутаторы (add_new, set_lang, remove, rename_method) пишут ChangeEvent.
  - Метод, помеченный remove, остаётся в _items с is_deleted=True.
"""
from datetime import datetime
from typing import Dict, List, Optional

from core.change_log import change_log, ChangeEvent
from core.method_item import MethodItem
from core.constants import IDCOL_KIND_METHOD

class MethodCollection:
    """Коллекция методов экземпляра объекта сцены."""

    def __init__(self, element_id: int, collection_manager=None):
        self.element_id = element_id
        self._collection_manager = collection_manager
        self._items: Dict[str, MethodItem] = {}

    # ------------------------------------------------------------------
    # Наполнение
    # ------------------------------------------------------------------
    def add(self, method: MethodItem):
        """
        Добавляет метод с учётом приоритета order.
        Меньший order приоритетнее. Более приоритетный НЕ затирается.
        """
        existing = self._items.get(method.c_name)
        if existing is None or method.order < existing.order:
            self._items[method.c_name] = method

    @classmethod
    def from_raw_rows(cls, element_id: int, rows: List[tuple],
                      collection_manager=None) -> "MethodCollection":
        col = cls(element_id, collection_manager)
        for r in rows:
            real_id = int(r[0]) if r[0] is not None else -1
            c_name = r[1]
            order = r[3] if len(r) > 3 and r[3] is not None else 1
            defined_in_version_id = r[4] if len(r) > 4 else None
            owner_class_id = r[5] if len(r) > 5 and r[5] is not None else 0
            i_lang = r[6] if len(r) > 6 and r[6] is not None else 3
            dt_start = r[7] if len(r) > 7 else None
            dt_end = r[8] if len(r) > 8 else None

            col.add(MethodItem(
                id=real_id,
                c_name=str(c_name),
                owner_class_id=int(owner_class_id),
                i_lang=int(i_lang),
                dt_start=dt_start,
                dt_end=dt_end,
                order=int(order),
                defined_in_version_id=defined_in_version_id,
            ))
        return col

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------
    def get(self, c_name: str) -> Optional[MethodItem]:
        return self._items.get(c_name)

    def all_ordered(self) -> List[MethodItem]:
        return sorted(self._items.values(), key=lambda m: (m.order, m.c_name))

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, c_name: str) -> bool:
        return c_name in self._items

    # ------------------------------------------------------------------
    # Добавление нового метода
    # ------------------------------------------------------------------
    def add_new(self, method: MethodItem) -> Optional[MethodItem]:
        """
        Добавляет новый метод. Присваивает уникальный отрицательный ID
        (DB-ID) и сквозной idCol (через CollectionManager).
        Уникальность имени в пределах родителя.
        """
        if not method.c_name:
            return None
        if method.c_name in self._items:
            return None

        method.id = (self._collection_manager.next_negative_db_id()
                     if self._collection_manager else -1)

        method.is_new = True
        method.is_changed = True
        method.order = 1
        method.is_from_qt = False

        # --- НОВОЕ (v7.2, Этап 1): сквозной idCol ---
        if self._collection_manager is not None:
            method.id_col = self._collection_manager.next_id_col()
            method.owner_element_id = self.element_id
            self._collection_manager.register_idcol(method, IDCOL_KIND_METHOD)
        else:
            # Без менеджера idCol остаётся 0 — навигация по idCol невозможна,
            # но метод всё равно добавляется (обратная совместимость).
            method.id_col = 0
            method.owner_element_id = self.element_id

        self._items[method.c_name] = method

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='method_add',
            element_id=self.element_id,
            target_id=method.id,
            target_name=method.c_name,
            old_value=None,
            new_value=method.id,
            source='user_edit',
            id_col=method.id_col,
        ))
        return method
    # ------------------------------------------------------------------
    # Изменение
    # ------------------------------------------------------------------
    def set_lang(self, c_name: str, i_lang: int) -> bool:
        """Меняет i_lang метода. Возвращает True, если изменилось. Пишет method_lang."""
        m = self._items.get(c_name)
        if m is None:
            return False
        if m.i_lang == i_lang:
            return False
        old_lang = m.i_lang
        m.i_lang = i_lang
        m.is_changed = True
        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='method_lang',
            element_id=self.element_id,
            target_id=m.id,
            target_name=c_name,
            old_value=old_lang,
            new_value=i_lang,
            source='user_edit',
            id_col=getattr(m, 'id_col', None),
        ))
        return True


    def rename_method(self, old_cname: str, new_cname: str) -> bool:
        """
        Переименовать метод. Уникальность имени в пределах родителя.
        method.id НЕ меняется. Пишет method_meta.
        """
        if not new_cname or new_cname == old_cname:
            return False
        if old_cname not in self._items:
            return False
        if new_cname in self._items:
            return False

        m = self._items.pop(old_cname)
        m.c_name = new_cname
        m.is_changed = True
        self._items[new_cname] = m

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='method_meta',
            element_id=self.element_id,
            target_id=m.id,
            target_name=new_cname,
            old_value=old_cname,
            new_value=new_cname,
            source='user_edit',
            extra={'rename': True, 'old_cname': old_cname},
            id_col=getattr(m, 'id_col', None),
        ))
        return True


    def remove(self, c_name: str) -> bool:
        """
        Помечает метод на удаление (is_deleted=True). Из _items не удаляет.
        Пишет method_delete.
        """
        m = self._items.get(c_name)
        if m is None:
            return False
        if getattr(m, 'is_deleted', False):
            return True
        m.is_deleted = True
        m.is_changed = True
        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='method_delete',
            element_id=self.element_id,
            target_id=m.id,
            target_name=c_name,
            old_value=False,
            new_value=True,
            source='user_edit',
            id_col=getattr(m, 'id_col', None),
        ))
        return True


    # ------------------------------------------------------------------
    # Для сохранения
    # ------------------------------------------------------------------
    def get_changed(self) -> List[MethodItem]:
        return [m for m in self.all_ordered() if m.is_changed]

    def mark_saved(self):
        for m in self._items.values():
            m.is_changed = False
            m.is_deleted = False
            m.is_new = False