# core/domain_event.py
# -*- coding: utf-8 -*-
"""
Доменное событие — каркас для будущего Undo/Redo (Этап 8+).

НЕ используется в Этапах 0–7. Введён сейчас, чтобы зафиксировать контракт:
любое атомарное изменение модели может быть описано парой
(old_value, new_value) + идентификатором объекта (id_col) + db_id,
достаточным для отката через ту же точку входа
CollectionManager.update_property_value_by_id_col(...).

Отличие от ChangeEvent:
  - ChangeEvent   — для UI-реактивности и лога (мгновенно, много событий).
  - DomainEvent   — для Undo/Redo (только значимые изменения, с undo_hint).

Поля:
  kind       : тип изменения ('prop_value' | 'prop_meta' | 'method_add' | ...).
  id_col     : объект в коллекции (навигация).
  db_id      : DB-id объекта (персистентность), может быть < 0 для новых.
  old_value  : прежнее значение.
  new_value  : новое значение.
  undo_hint  : {'cname': ..., 'source': ...} — как откатить через
               update_property_value_by_id_col(...).
  timestamp  : момент события.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class DomainEvent:
    """Атомарное доменное изменение, пригодное для отката."""

    kind: str                       # 'prop_value' | 'prop_meta' | 'method_add' | ...
    id_col: int                     # объект в коллекции (навигация)
    db_id: Optional[int]            # DB-id объекта (персистентность), может быть < 0
    old_value: Any
    new_value: Any
    undo_hint: Optional[dict] = None  # {'cname': ..., 'source': ...} — как откатить
    timestamp: datetime = field(default_factory=datetime.now)

    def is_reversible(self) -> bool:
        return self.undo_hint is not None