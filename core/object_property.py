# core/object_property.py
# -*- coding: utf-8 -*-
"""
Одна строка objpropcol — свойство экземпляра объекта на сцене.
Соответствует структуре из f_build_objpropcol.

v7.2 (Этап 0):
  - добавлены id_col (сквозная навигация в коллекции) и owner_element_id
    (обратная ссылка на элемент-владелец).
  - Оба поля НЕ заполняются в __post_init__. Их присваивает атомарно
    CollectionManager.init_property_collection (Этап 1), чтобы гарантировать
    уникальность id_col в пределах всей коллекции.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ObjectProperty:
    """Свойство экземпляра объекта сцены."""

    # --- Базовые идентификаторы и значение ---
    id: int  # class_version_properties.id (-1 / отрицательный для новых)
    cname: str  # системное имя свойства
    order: int  # порядок в линии крови (1 = локальное)
    value: str  # текущее значение (всегда строка)

    # --- НОВОЕ (v7.2, Этап 0): навигация в памяти ---
    id_col: int = 0            # сквозной уникальный идентификатор в коллекции
    owner_element_id: int = 0  # element_id владельца (может быть отрицательным)

    # --- Метаданные из БД / моста ---
    typevalue: int = 0
    sourcevalue: Optional[str] = None
    typesourcevalue: Optional[str] = None
    fuuncselectionvalue: Optional[str] = None
    bridgecalcset: Optional[str] = None
    bridgecalcget: Optional[str] = None
    defined_in_version_id: Optional[int] = None

    # --- Переопределения v8.1 ---
    override_id: Optional[int] = None
    ui_label_ru: Optional[str] = None
    editor_type: Optional[str] = None
    qt_target: Optional[str] = None
    translation_strategy: Optional[str] = None
    isdefaultepr: Optional[bool] = None
    blob_value: Optional[bytes] = None
    blob_name: Optional[str] = None
    is_blob: bool = False
    owner_version_id: Optional[int] = None
    is_from_qt: bool = False

    # --- Поля идентичности v9 (Этап 1) ---
    idVersion: Optional[int] = None
    chngID: Optional[int] = None
    chngIDVersion: Optional[int] = None

    # --- Флаги жизненного цикла v9 ---
    isDelete: bool = False
    isInherited: bool = False
    isDirty: bool = False

    # --- ТУПОЙ ФЛАГ ИЗМЕНЕНИЯ (v9) ---
    is_changed: bool = False

    # --- Legacy-флаги (обратная совместимость) ---
    is_property_changed: bool = False
    is_deleted: bool = False

    # --- Снимки для отслеживания изменений ---
    initial_value: str = field(default="")
    initial_meta: Optional[dict] = field(default=None)

    def __post_init__(self):
        if not self.initial_value:
            self.initial_value = self.value

        if self.initial_meta is None:
            self.initial_meta = {
                'ui_label_ru': self.ui_label_ru,
                'editor_type': self.editor_type,
                'qt_target': self.qt_target,
                'translation_strategy': self.translation_strategy,
                'isdefaultepr': self.isdefaultepr,
                'bridgecalcset': self.bridgecalcset,
                'bridgecalcget': self.bridgecalcget,
                'fuuncselectionvalue': self.fuuncselectionvalue,
                'typevalue': self.typevalue,
                'is_blob': self.is_blob,
            }

    def mark_saved(self):
        """После сохранения — фиксируем новое состояние и сбрасываем все флаги."""
        self.initial_value = self.value
        self.initial_meta = {
            'ui_label_ru': self.ui_label_ru,
            'editor_type': self.editor_type,
            'qt_target': self.qt_target,
            'translation_strategy': self.translation_strategy,
            'isdefaultepr': self.isdefaultepr,
            'bridgecalcset': self.bridgecalcset,
            'bridgecalcget': self.bridgecalcget,
            'fuuncselectionvalue': self.fuuncselectionvalue,
            'typevalue': self.typevalue,
            'is_blob': self.is_blob,
        }

        self.is_property_changed = False
        self.is_deleted = False
        self.isDirty = False
        self.isDelete = False
        self.is_changed = False