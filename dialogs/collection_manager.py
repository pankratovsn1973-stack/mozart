# Полный путь: dialogs/collection_manager.py
# -*- coding: utf-8 -*-
"""
Менеджер коллекции элементов сцены редактора классов.
Хранит в памяти ВСЕ состояние сцены: данные элементов и их графические представления.
Обеспечивает мгновенный доступ к QGraphicsItem по ID из базы данных для операций выделения,
перемещения, ресайза и удаления.
Использует отрицательные ID (-1, -2...) для новых объектов до сохранения в БД.
Не зависит от UI, является чистой in-memory моделью состояния.
"""

from typing import Dict, List, Set, Optional, Any
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem


class CollectionManager:
    """
    Централизованное хранилище состояния сцены.

    Свойства:
    - elements: Dict[int, Dict] - Данные элементов (ключ = ID из БД или отрицательный).
      Структура значения: {id, parent_id, calias, cclass, x, y, width, height, properties, is_new}
    - graphics_items: Dict[int, QGraphicsItem] - Графические объекты на сцене.
      Ключ соответствует ключу в elements. Позволяет управлять графикой напрямую по ID.
    - selected_ids: Set[int] - Набор ID выделенных элементов.
    - deleted_ids: Set[int] - Набор ID элементов, помеченных на удаление.
    - next_id: int - Счетчик генерации отрицательных ID (начинается с -1).

    Методы:
    - add_element(element_data, graphic_item) -> int : Добавление элемента и его графики.
    - link_graphic_item(element_id, graphic_item) : Привязка графики к существующему элементу.
    - get_element(element_id) -> Optional[Dict] : Получение данных по ID.
    - get_graphic_item(element_id) -> Optional[QGraphicsItem] : Получение графики по ID.
    - update_element_data(element_id, data) : Обновление данных и синхронизация графики.
    - remove_element(element_id) : Удаление элемента и его графики со сцены.
    - select_element(element_id, additive) : Управление выделением.
    - clear_selection() : Сброс выделения.
    - move_selected(dx, dy) : Перемещение всех выделенных элементов (данные + графика).
    - resize_selected(dw, dh) : Изменение размера выделенных элементов.
    - delete_selected() : Удаление всех выделенных элементов.
    - align_selected(alignment) : Выравнивание выделенных ('top', 'left' и т.д.).
    - equalize_sizes() : Приведение размеров выделенных к последнему выбранному.
    - get_inserts() -> List[Dict] : Список элементов для INSERT (ID < 0).
    - get_updates() -> List[Dict] : Список элементов для UPDATE (ID > 0).
    - get_deletes() -> List[int] : Список ID для физического удаления.
    """

    def __init__(self):
        self.elements: Dict[int, Dict] = {}
        self.graphics_items: Dict[int, QGraphicsItem] = {}
        self.selected_ids: Set[int] = set()
        self.deleted_ids: Set[int] = set()
        self.next_id: int = -1

    def add_element(self, element_data: Dict, graphic_item: Optional[QGraphicsItem] = None) -> int:
        """
        Добавляет новый элемент в коллекцию и присваивает ему отрицательный ID.

        Args:
            element_data: Словарь свойств элемента (без поля 'id').
            graphic_item: Опциональная ссылка на QGraphicsItem. Если передана, сразу регистрируется.

        Returns:
            int: Присвоенный отрицательный ID.
        """
        new_id = self.next_id
        self.next_id -= 1

        # Сохраняем данные
        data_copy = dict(element_data)
        data_copy['id'] = new_id
        data_copy['is_new'] = True
        self.elements[new_id] = data_copy

        # Сразу связываем графику, если она есть
        if graphic_item is not None:
            self.graphics_items[new_id] = graphic_item

        return new_id

    def link_graphic_item(self, element_id: int, graphic_item: QGraphicsItem):
        """
        Связывает существующий элемент данных с его графическим представлением.
        Используется при загрузке из БД, когда сначала создаются данные, а потом рендерится сцена.

        Args:
            element_id: ID элемента в коллекции.
            graphic_item: Объект QGraphicsItem на сцене.
        """
        if element_id in self.elements:
            self.graphics_items[element_id] = graphic_item

    def get_element(self, element_id: int) -> Optional[Dict]:
        """Возвращает словарь данных элемента по ID."""
        return self.elements.get(element_id)

    def get_graphic_item(self, element_id: int) -> Optional[QGraphicsItem]:
        """Возвращает графический объект по ID. Критично для операций над сценой."""
        return self.graphics_items.get(element_id)

    def update_element_data(self, element_id: int, data: Dict):
        """
        Обновляет данные элемента и автоматически применяет изменения к графике, если она существует.

        Args:
            element_id: ID элемента.
            data: Словарь обновляемых полей (x, y, width, height и др.).
        """
        if element_id in self.elements:
            self.elements[element_id].update(data)

            # Синхронизация графики
            item = self.graphics_items.get(element_id)
            if item and hasattr(item, 'set_geometry'):
                x = data.get('x', self.elements[element_id].get('x'))
                y = data.get('y', self.elements[element_id].get('y'))
                w = data.get('width', self.elements[element_id].get('width'))
                h = data.get('height', self.elements[element_id].get('height'))
                item.set_geometry(x, y, w, h)

    def remove_element(self, element_id: int):
        """
        Удаляет элемент из коллекции и убирает его графику со сцены.

        Args:
            element_id: ID удаляемого элемента.
        """
        if element_id in self.elements:
            self.deleted_ids.add(element_id)

            # Удаляем графику со сцены
            item = self.graphics_items.pop(element_id, None)
            if item and item.scene():
                item.scene().removeItem(item)

            del self.elements[element_id]
            self.selected_ids.discard(element_id)

    def select_element(self, element_id: int, additive: bool = False):
        """Управляет состоянием выделения."""
        if element_id not in self.elements:
            return

        if not additive:
            self.clear_selection()
        self.selected_ids.add(element_id)

    def clear_selection(self):
        """Снимает выделение со всех элементов."""
        self.selected_ids.clear()

    def get_selected_elements(self) -> List[Dict]:
        """Возвращает список данных выделенных элементов."""
        return [self.elements[eid] for eid in self.selected_ids if eid in self.elements]

    def move_selected(self, dx: float, dy: float):
        """
        Перемещает все выделенные элементы на вектор (dx, dy).
        Обновляет И данные в памяти, И позицию на сцене.
        """
        for eid in list(self.selected_ids):
            if eid in self.elements:
                elem = self.elements[eid]
                elem['x'] = elem.get('x', 0) + dx
                elem['y'] = elem.get('y', 0) + dy

                # Двигаем графику
                item = self.graphics_items.get(eid)
                if item:
                    item.moveBy(dx, dy)

    def resize_selected(self, dw: float, dh: float):
        """Изменяет размер выделенных элементов."""
        min_w, min_h = 20, 15
        for eid in list(self.selected_ids):
            if eid in self.elements:
                elem = self.elements[eid]
                new_w = max(min_w, elem.get('width', 100) + dw)
                new_h = max(min_h, elem.get('height', 30) + dh)
                elem['width'] = new_w
                elem['height'] = new_h

                # Меняем размер графики
                item = self.graphics_items.get(eid)
                if item and hasattr(item, 'resize'):
                    item.resize(new_w, new_h)

    def delete_selected(self):
        """Удаляет все выделенные элементы."""
        for eid in list(self.selected_ids):
            self.remove_element(eid)
        self.selected_ids.clear()

    def align_selected(self, alignment: str):
        """Выравнивает выделенные элементы по заданной стороне."""
        selected = self.get_selected_elements()
        if len(selected) < 2:
            return

        ref_val = None
        key_map = {'top': 'y', 'left': 'x', 'bottom': 'y', 'right': 'x'}

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
                if alignment in ('top', 'left'):
                    e[key_map[alignment]] = ref_val
                else:
                    e[key_map[alignment]] = ref_val - e.get('height' if alignment == 'bottom' else 'width', 0)

                # Применяем к графике
                item = self.graphics_items.get(e['id'])
                if item:
                    if alignment == 'top':
                        item.setY(ref_val)
                    elif alignment == 'left':
                        item.setX(ref_val)
                    elif alignment == 'bottom':
                        item.setY(ref_val - e['height'])
                    elif alignment == 'right':
                        item.setX(ref_val - e['width'])

    def equalize_sizes(self):
        """Приводит размеры всех выделенных элементов к размеру последнего выбранного."""
        last = self.get_last_selected()
        if not last:
            return

        ref_w = last.get('width', 100)
        ref_h = last.get('height', 30)

        for elem in self.get_selected_elements():
            if elem['id'] != last['id']:
                elem['width'] = ref_w
                elem['height'] = ref_h

                item = self.graphics_items.get(elem['id'])
                if item and hasattr(item, 'resize'):
                    item.resize(ref_w, ref_h)

    def get_last_selected(self) -> Optional[Dict]:
        """Возвращает последний выделенный элемент (для привязки выравнивания/размера)."""
        if not self.selected_ids:
            return None
        last_id = list(self.selected_ids)[-1]
        return self.elements.get(last_id)

    def get_inserts(self) -> List[Dict]:
        """Элементы для INSERT (ID < 0)."""
        return [v for k, v in self.elements.items() if k < 0]

    def get_updates(self) -> List[Dict]:
        """Элементы для UPDATE (ID > 0)."""
        return [v for k, v in self.elements.items() if k > 0 and k not in self.deleted_ids]

    def get_deletes(self) -> List[int]:
        """ID элементов для DELETE."""
        return list(self.deleted_ids)

    def get_next_id(self) -> int:
        """Предпросмотр следующего ID без инкремента."""
        return self.next_id - 1