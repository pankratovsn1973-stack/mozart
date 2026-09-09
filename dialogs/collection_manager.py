# Полный путь: dialogs/collection_manager.py
# -- coding: utf-8 --
"""
Менеджер коллекции элементов сцены редактора классов.
Хранит в памяти ВСЕ состояние сцены: данные элементов и их графические представления.
Обеспечивает мгновенный доступ к QGraphicsItem по ID из базы данных для операций выделения,
перемещения, ресайза и удаления.
Использует отрицательные ID (-1, -2...) для новых объектов до сохранения в БД.
Не зависит от UI, является чистой in-memory моделью состояния.

Все поля приватные (_prefix). Внешний доступ — только через публичные методы с валидацией.
"""
isDebug = 1  # 1 = печатать отладочные принты, 0 = тихо

from typing import Dict, List, Set, Optional, Any, Tuple
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem


class CollectionManager:
    """
    Централизованное хранилище состояния сцены с защищённым API.
    """

    def __init__(self):
        self._elements: Dict[int, Dict] = {}
        self._graphics_items: Dict[int, QGraphicsItem] = {}
        self._selected_ids: Set[int] = set()
        self._deleted_ids: Set[int] = set()
        self._next_id: int = -1
        self._active_container_id: Optional[int] = None
        self._last_selected_id: Optional[int] = None

    # =========================================================================
    # READ-ONLY СВОЙСТВА
    # =========================================================================

    @property
    def selected_ids(self) -> frozenset:
        return frozenset(self._selected_ids)

    @property
    def elements_count(self) -> int:
        return len(self._elements)

    @property
    def active_container_id(self) -> Optional[int]:
        return self._active_container_id

    @property
    def last_selected_id(self) -> Optional[int]:
        return self._last_selected_id

    # =========================================================================
    # БЕЗОПАСНОЕ ЧТЕНИЕ
    # =========================================================================

    def get_element(self, element_id: int) -> Optional[Dict]:
        elem = self._elements.get(element_id)
        return dict(elem) if elem else None

    def get_graphic_item(self, element_id: int) -> Optional[QGraphicsItem]:
        return self._graphics_items.get(element_id)

    def get_selected_elements(self) -> List[Dict]:
        return [dict(self._elements[eid]) for eid in self._selected_ids if eid in self._elements]

    def get_last_selected(self) -> Optional[Dict]:
        if not self._last_selected_id:
            return None
        elem = self._elements.get(self._last_selected_id)
        return dict(elem) if elem else None

    # =========================================================================
    # УПРАВЛЕНИЕ ЭЛЕМЕНТАМИ
    # =========================================================================

    def add_element(self, element_data: Dict, graphic_item: Optional[QGraphicsItem] = None) -> int:
        new_id = self._next_id
        self._next_id -= 1
        data_copy = dict(element_data)
        data_copy['id'] = new_id
        data_copy['is_new'] = True
        self._elements[new_id] = data_copy
        if graphic_item is not None:
            self._graphics_items[new_id] = graphic_item
        return new_id

    def link_graphic_item(self, element_id: int, graphic_item: QGraphicsItem):
        if element_id in self._elements:
            self._graphics_items[element_id] = graphic_item

    def update_element_data(self, element_id: int, data: Dict, from_graphics: bool = False):
        if element_id not in self._elements:
            return
        self._elements[element_id].update(data)
        if not from_graphics:
            item = self._graphics_items.get(element_id)
            if item and hasattr(item, 'set_geometry'):
                elem = self._elements[element_id]
                item.set_geometry(
                    elem.get('x', 0), elem.get('y', 0),
                    elem.get('width', 100), elem.get('height', 30)
                )

    def remove_element(self, element_id: int):
        if element_id not in self._elements:
            return
        self._deleted_ids.add(element_id)
        item = self._graphics_items.pop(element_id, None)
        if item and item.scene():
            item.scene().removeItem(item)
        del self._elements[element_id]
        self._selected_ids.discard(element_id)
        if self._last_selected_id == element_id:
            self._last_selected_id = next(iter(self._selected_ids), None) if self._selected_ids else None
        if self._active_container_id == element_id:
            self._active_container_id = None

    # =========================================================================
    # ГРУППОВОЕ ВЫДЕЛЕНИЕ (с валидацией контейнера)
    # =========================================================================

    def add_to_selection(self, element_id: int) -> bool:
        if element_id not in self._elements:
            return True
        parent_id = self._elements[element_id].get('parent_id')
        if self._selected_ids and parent_id != self._active_container_id:
            return False
        self._selected_ids.add(element_id)
        self._active_container_id = parent_id
        self._last_selected_id = element_id
        if isDebug:
            print(f"[DEBUG CM.add_to_selection] id={element_id}, selected={self._selected_ids}, last={self._last_selected_id}")
        return True

    def remove_from_selection(self, element_id: int):
        self._selected_ids.discard(element_id)
        if self._last_selected_id == element_id:
            self._last_selected_id = next(iter(self._selected_ids), None) if self._selected_ids else None
        if not self._selected_ids:
            self._active_container_id = None
        if isDebug:
            print(f"[DEBUG CM.remove_from_selection] id={element_id}, selected={self._selected_ids}, last={self._last_selected_id}")

    def set_selection(self, element_ids: List[int], container_id: Optional[int]):
        self._selected_ids.clear()
        valid_ids = [eid for eid in element_ids if eid in self._elements]
        self._selected_ids.update(valid_ids)
        self._active_container_id = container_id
        self._last_selected_id = valid_ids[-1] if valid_ids else None
        if isDebug:
            print(f"[DEBUG CM.set_selection] ids={valid_ids}, container={container_id}, last={self._last_selected_id}")

    def clear_selection(self):
        self._selected_ids.clear()
        self._active_container_id = None
        self._last_selected_id = None
        if isDebug:
            print(f"[DEBUG CM.clear_selection] cleared")

    def select_element(self, element_id: int, additive: bool = False) -> bool:
        if element_id not in self._elements:
            return True
        if not additive:
            self.clear_selection()
            self._selected_ids.add(element_id)
            self._active_container_id = self._elements[element_id].get('parent_id')
            self._last_selected_id = element_id
            if isDebug:
                print(f"[DEBUG CM.select_element] id={element_id}, additive=False, selected={self._selected_ids}, last={self._last_selected_id}")
            return True
        return self.add_to_selection(element_id)

    # =========================================================================
    # ГРУППОВЫЕ ОПЕРАЦИИ
    # =========================================================================

    def move_selected(self, dx: float, dy: float):
        if not self._selected_ids:
            return
        if isDebug:
            print(f"[DEBUG CM.move_selected] dx={dx}, dy={dy}, count={len(self._selected_ids)}")
        for eid in list(self._selected_ids):
            if eid in self._elements:
                elem = self._elements[eid]
                elem['x'] = elem.get('x', 0) + dx
                elem['y'] = elem.get('y', 0) + dy
                item = self._graphics_items.get(eid)
                if item:
                    item.moveBy(dx, dy)

    def resize_selected(self, dw: float, dh: float):
        if not self._selected_ids:
            return
        min_w, min_h = 20, 15
        if isDebug:
            print(f"[DEBUG CM.resize_selected] dw={dw}, dh={dh}, count={len(self._selected_ids)}")
        for eid in list(self._selected_ids):
            if eid in self._elements:
                elem = self._elements[eid]
                new_w = max(min_w, elem.get('width', 100) + dw)
                new_h = max(min_h, elem.get('height', 30) + dh)
                elem['width'] = new_w
                elem['height'] = new_h
                item = self._graphics_items.get(eid)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, new_w, new_h)

    def delete_selected(self):
        for eid in list(self._selected_ids):
            self.remove_element(eid)
        self._selected_ids.clear()
        self._active_container_id = None
        self._last_selected_id = None

    def align_selected(self, alignment: str):
        selected = self.get_selected_elements()
        if len(selected) < 2:
            return
        key_map = {'top': 'y', 'left': 'x', 'bottom': 'y', 'right': 'x'}
        ref_val = None
        if alignment == 'top':
            ref_val = min(e.get('y', 0) for e in selected)
        elif alignment == 'left':
            ref_val = min(e.get('x', 0) for e in selected)
        elif alignment == 'bottom':
            ref_val = max(e.get('y', 0) + e.get('height', 30) for e in selected)
        elif alignment == 'right':
            ref_val = max(e.get('x', 0) + e.get('width', 100) for e in selected)
        if ref_val is not None:
            for e in selected:
                eid = e['id']
                if eid not in self._elements:
                    continue
                elem = self._elements[eid]
                if alignment in ('top', 'left'):
                    elem[key_map[alignment]] = ref_val
                else:
                    dim = 'height' if alignment == 'bottom' else 'width'
                    elem[key_map[alignment]] = ref_val - elem.get(dim, 0)
                item = self._graphics_items.get(eid)
                if item:
                    if alignment == 'top':
                        item.setY(ref_val)
                    elif alignment == 'left':
                        item.setX(ref_val)
                    elif alignment == 'bottom':
                        item.setY(ref_val - elem['height'])
                    elif alignment == 'right':
                        item.setX(ref_val - elem['width'])

    def equalize_width(self):
        selected = self.get_selected_elements()
        if len(selected) < 2:
            return
        max_w = max(e.get('width', 100) for e in selected)
        for e in selected:
            eid = e['id']
            if eid in self._elements:
                self._elements[eid]['width'] = max_w
                item = self._graphics_items.get(eid)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, max_w, self._elements[eid].get('height', 30))

    def equalize_height(self):
        selected = self.get_selected_elements()
        if len(selected) < 2:
            return
        max_h = max(e.get('height', 30) for e in selected)
        for e in selected:
            eid = e['id']
            if eid in self._elements:
                self._elements[eid]['height'] = max_h
                item = self._graphics_items.get(eid)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, self._elements[eid].get('width', 100), max_h)

    def equalize_sizes(self):
        last = self.get_last_selected()
        if not last:
            return
        ref_w = last.get('width', 100)
        ref_h = last.get('height', 30)
        for elem in self.get_selected_elements():
            eid = elem['id']
            if eid != last['id'] and eid in self._elements:
                self._elements[eid]['width'] = ref_w
                self._elements[eid]['height'] = ref_h
                item = self._graphics_items.get(eid)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, ref_w, ref_h)

    # =========================================================================
    # СЕРИАЛИЗАЦИЯ ДЛЯ СОХРАНЕНИЯ
    # =========================================================================

    def get_inserts(self) -> List[Dict]:
        return [dict(v) for k, v in self._elements.items() if k < 0]

    def get_updates(self) -> List[Dict]:
        return [dict(v) for k, v in self._elements.items() if k > 0 and k not in self._deleted_ids]

    def get_deletes(self) -> List[int]:
        return list(self._deleted_ids)

    def get_next_id(self) -> int:
        return self._next_id - 1