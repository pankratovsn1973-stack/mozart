# core/change_log.py
# -*- coding: utf-8 -*-
"""
Журнал изменений модели Mozart ERP.

v7.2 (Этап 0): в ChangeEvent добавлено поле id_col — сквозной идентификатор
объекта в коллекции. Именно по нему Inspector и реактивные слоты находят
узел, а не по DB-ID (target_id).

v7.2 FIX: format_line() больше НЕ выводит elem= (DB-ID элемента) и id= (DB-ID
объекта) как ключи навигации. Для навигации используется ТОЛЬКО idCol.
DB-ID убран из лога, потому что он неуникален между типами объектов
(элемент/свойство/метод/сигнал могут иметь одинаковый DB-ID).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, List, Optional
from collections import deque
import threading


@dataclass
class ChangeEvent:
    timestamp: datetime
    kind: str          # 'prop_value' | 'prop_meta' | 'prop_blob' | 'prop_delete' | 'prop_add'
                       # | 'method_lang' | 'method_delete' | 'method_add' | 'method_meta'
                       # | 'element_add' | 'element_delete' | 'element_reparent'
                       # | 'collection_clear'
    element_id: int    # DB-ID элемента сцены (НЕ уникален между типами; только для служебных нужд)
    target_id: int     # DB-ID свойства/метода/сигнала (НЕ уникален между типами)
    target_name: str   # cname / c_name / calias — только для читаемости лога, не ключ
    old_value: Any
    new_value: Any
    source: str = ""   # 'user_edit' | 'select' | 'init' | 'auto_sync' | 'program'
                       # | 'silent' | 'vizivig' | 'user_edit_reset'
    extra: dict = field(default_factory=dict)

    # Сквозной идентификатор объекта в коллекции (единственный ключ навигации).
    # Для element_* — id_col элемента; для prop_*/method_*/signal_* — id_col
    # соответствующего вложенного объекта.
    # Может быть None только для 'collection_clear' и 'element_delete'
    # (элемент уже вылетел из индекса).
    id_col: Optional[int] = None

    def format_line(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S.%f")[:-3]

        # v7.2 FIX: для навигации — только idCol. DB-ID не выводим.
        if self.id_col is not None:
            nav_part = f"idcol={self.id_col}"
        else:
            nav_part = "idcol=—"

        return (f"[{ts}] [{self.kind}] "
                f"{nav_part} {self.target_name}: "
                f"{self.old_value!r} → {self.new_value!r} (src={self.source})")


class ChangeLog:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, maxlen=5000):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._events = deque(maxlen=maxlen)
                    inst._subscribers: List[Callable] = []
                    inst._mutex = threading.RLock()
                    cls._instance = inst
        return cls._instance

    def record(self, event: ChangeEvent):
        with self._mutex:
            self._events.append(event)
            subscribers = list(self._subscribers)
        for cb in subscribers:
            try:
                cb(event)
            except Exception:
                pass

    def subscribe(self, cb):
        with self._mutex:
            if cb not in self._subscribers:
                self._subscribers.append(cb)

    def unsubscribe(self, cb):
        with self._mutex:
            try:
                self._subscribers.remove(cb)
            except ValueError:
                pass

    def snapshot(self) -> List[ChangeEvent]:
        with self._mutex:
            return list(self._events)

    def clear(self):
        with self._mutex:
            self._events.clear()


change_log = ChangeLog()