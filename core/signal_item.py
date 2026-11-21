# core/signal_item.py
# -*- coding: utf-8 -*-
"""
Единая модель сигнала экземпляра объекта сцены (или класса).

v7.2 (Этап 0): введён для замены сырых dict в sub_signals.
Позволяет регистрировать сигналы в общем индексе idCol так же, как
свойства и методы, и единообразно сохранять их в БД.

Поля:
  - id            : DB-id строки class_erp.signal; None = унаследован,
                    ещё не сохранялся в БД как собственный сигнал.
  - c_signal      : системное имя сигнала (например, 'clicked').
  - id_method     : DB-id привязанного метода-обработчика (или None).
  - id_col        : сквозной уникальный идентификатор в коллекции.
  - owner_element_id : element_id владельца (может быть отрицательным).
  - флаги жизненного цикла: is_new / is_changed / is_deleted /
                    isInherited / isDirty (по аналогии с MethodItem).

Заполнение id_col / owner_element_id — атомарно в
CollectionManager.init_signal_collection (Этап 1).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SignalItem:
    """Метаданные сигнала (без обработчика)."""

    # DB-id строки class_erp.signal; None = унаследован, ещё не сохранялся
    id: Optional[int]
    c_signal: str
    id_method: Optional[int] = None

    # --- НОВОЕ (v7.2, Этап 0): навигация в памяти ---
    id_col: int = 0
    owner_element_id: int = 0

    # --- Флаги жизненного цикла (по аналогии с MethodItem) ---
    is_new: bool = False
    is_changed: bool = False
    is_deleted: bool = False
    isInherited: bool = False
    isDirty: bool = False

    def __repr__(self) -> str:
        return (f"SignalItem(id={self.id}, c_signal={self.c_signal!r}, "
                f"id_method={self.id_method}, id_col={self.id_col})")