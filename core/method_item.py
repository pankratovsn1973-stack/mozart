# core/method_item.py
# -*- coding: utf-8 -*-
"""
Метаданные одного метода экземпляра объекта сцены (или класса).
Код метода (txt_method) НЕ хранится здесь — он загружается лениво
при открытии MethodsDialog и сохраняется сразу в БД.

v7.2 (Этап 0):
  - добавлены id_col (сквозная навигация в коллекции) и owner_element_id
    (обратная ссылка на элемент-владелец).
  - Оба поля НЕ заполняются в __post_init__. Их присваивает атомарно
    CollectionManager.init_method_collection (Этап 1) и
    MethodCollection.add_new — через manager.next_id_col() / register_idcol.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MethodItem:
    """Метаданные метода (без кода)."""

    id: int
    c_name: str
    owner_class_id: int
    i_lang: int = 3
    dt_start: Optional[datetime] = None
    dt_end: Optional[datetime] = None
    is_from_qt: bool = False
    is_changed: bool = False
    is_deleted: bool = False       # legacy-флаг: метод помечен на удаление
    is_new: bool = False

    # --- Линия крови ---
    order: int = 1
    defined_in_version_id: Optional[int] = None
    inherited_from_element_id: Optional[int] = None
    is_overridden: bool = False

    # --- Поля идентичности v9 (Этап 1) ---
    idVersion: Optional[int] = None
    chngID: Optional[int] = None
    chngIDVersion: Optional[int] = None
    isDelete: bool = False
    isInherited: bool = False
    isDirty: bool = False

    # --- НОВОЕ (v7.2, Этап 0): навигация в памяти ---
    id_col: int = 0
    owner_element_id: int = 0

    def is_inherited(self) -> bool:
        """True, если метод унаследован (order > 1)."""
        return self.order > 1