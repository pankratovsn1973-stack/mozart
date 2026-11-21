# dialogs/collection_manager.py
# -*- coding: utf-8 -*-
"""
Менеджер коллекции элементов сцены редактора классов.
v7.4 (STRICT IDCOL + DEFERRED GRAPHICS):
- _elements индексируется СТРОГО по id_col.
- _graphics_items индексируется СТРОГО по id_col.
- DB-ID (element_id) хранится внутри словаря элемента под ключом 'db_id'.
- Навигация, выделение, поиск, графика — ТОЛЬКО через id_col.
- DB-ID используется исключительно для сохранения/загрузки из БД.
- Отрисовка возможна только после ПОЛНОГО формирования коллекции.
"""
isDebug = 1
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Set, Optional, Any, Tuple
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem
from core.change_log import change_log, ChangeEvent
from core.constants import (
    IDCOL_KIND_ELEMENT, IDCOL_KIND_PROP, IDCOL_KIND_METHOD, IDCOL_KIND_SIGNAL,
    GEOMETRY_PROPS, ALLOWED_GEOMETRY_SOURCES,
)
from core.signal_item import SignalItem
from core.object_property import ObjectProperty
from core.object_property_collection import ObjectPropertyCollection
from core.method_collection import MethodCollection


class CollectionManager:
    """Централизованное хранилище состояния сцены с защищённым API."""

    def __init__(self):
        # _elements индексируется ПО id_col
        self._elements: Dict[int, Dict] = {}

        # _graphics_items индексируется ПО id_col
        self._graphics_items: Dict[int, QGraphicsItem] = {}

        # Обратный индекс: DB-ID → idCol. Нужен для операций сохранения (БД по DB-ID).
        self._db_id_to_id_col: Dict[int, int] = {}

        # Множества и ID для выделения — хранят idCol
        self._selected_idcols: Set[int] = set()
        self._active_container_idcol: Optional[int] = None
        self._last_selected_idcol: Optional[int] = None

        self._deleted_db_ids: Set[int] = set()
        self._lineages: Dict[int, List[Dict]] = {}

        # Единый счётчик отрицательных ID (DB-ID для новых элементов)
        self._next_negative_db_id: int = -1

        # Сквозной idCol
        self._next_id_col: int = 1

        # Индекс для быстрого поиска объекта по id_col (свойства, методы, сигналы)
        self._idcol_to_object: Dict[int, object] = {}
        self._idcol_kind: Dict[int, str] = {}

        # Тихий режим
        self._silent_depth: int = 0
    # =========================================================================
    # ТИХИЙ РЕЖИМ (silent_mode)
    # =========================================================================

    def begin_silent(self) -> None:
        """Входит в тихий режим (накапливается)."""
        self._silent_depth += 1

    def end_silent(self) -> None:
        """Выходит из тихого режима (не уходит в минус)."""
        if self._silent_depth > 0:
            self._silent_depth -= 1

    def is_silent(self) -> bool:
        """True, если активен тихий режим (в т.ч. вложенный)."""
        return self._silent_depth > 0

    @contextmanager
    def silent_mode(self):
        """
        Контекстный менеджер тихого режима.
        Запись в модель без SET-бриджей и без UI-реактивности.
        """
        self.begin_silent()
        try:
            yield
        finally:
            self.end_silent()



    # =========================================================================
    # ГЕНЕРАЦИЯ ID
    # =========================================================================
    def next_negative_db_id(self) -> int:
        """Генерирует уникальный отрицательный DB-ID для временного хранения."""
        nid = self._next_negative_db_id
        self._next_negative_db_id -= 1
        if self._next_negative_db_id < -1_000_000_000:
            raise RuntimeError("Исчерпан диапазон временных отрицательных DB-ID")
        return nid

    def next_id_col(self) -> int:
        """Выдаёт следующий сквозной idCol."""
        nid = self._next_id_col
        self._next_id_col += 1
        return nid

    # =========================================================================
    # ВНУТРЕННИЕ УТИЛИТЫ
    # =========================================================================
    def _get_db_id_by_id_col(self, id_col: int) -> Optional[int]:
        """Безопасно получает DB-ID элемента по его id_col."""
        elem = self._elements.get(id_col)
        return elem.get('db_id') if elem else None

    def _get_id_col_by_db_id(self, db_id: int) -> Optional[int]:
        """O(1): поиск id_col по DB-ID через обратный индекс."""
        if db_id is None:
            return None
        return self._db_id_to_id_col.get(db_id)


    # =========================================================================
    # УПРАВЛЕНИЕ ЭЛЕМЕНТАМИ (STRICT IDCOL)
    # =========================================================================
    def add_element_with_metadata(self, element_data: dict, donor_version_id: int, db_service) -> int:
        """
        Добавляет элемент и возвращает его id_col.
        element_data должен содержать 'parent_id' (DB-ID родителя).
        """
        from ide_core import goProject

        # Если DB-ID не задан, генерируем временный
        if 'db_id' not in element_data or element_data['db_id'] is None:
            element_data['db_id'] = self.next_negative_db_id()

        new_id_col = self.next_id_col()

        data_copy = dict(element_data)
        data_copy['id_col'] = new_id_col
        data_copy['is_new'] = True
        data_copy['is_saved'] = False
        data_copy['saved_version_id'] = None
        data_copy['property_collection'] = None
        data_copy['method_collection'] = None
        data_copy['lineage'] = []
        data_copy['donor_version_id'] = donor_version_id

        self._elements[new_id_col] = data_copy
        # ✅ Заполняем обратный индекс O(1)
        self._db_id_to_id_col[data_copy['db_id']] = new_id_col
        self.register_idcol(data_copy, IDCOL_KIND_ELEMENT)

        # Инициализация свойств от донора
        raw_props = []
        if donor_version_id and donor_version_id > 0:
            try:
                raw_props = goProject.class_registry.get_objpropcol_raw(int(donor_version_id))
            except (ValueError, TypeError):
                raw_props = []

        if raw_props:
            col = self.init_property_collection(data_copy['db_id'], raw_props)
            defaults = {'myx': '20', 'myy': '40', 'mywidth': '150', 'myheight': '30'}
            for key, val in defaults.items():
                prop = col.get(key)
                if prop is not None and not prop.value:
                    prop.value = val

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='element_add',
            element_id=data_copy['db_id'],
            target_id=data_copy['db_id'],
            target_name=data_copy.get('calias', ''),
            old_value=None,
            new_value=new_id_col,
            source='user_edit',
            id_col=new_id_col,
        ))
        return new_id_col

    def get_element_by_id_col(self, id_col: int) -> Optional[Dict]:
        """Возвращает данные элемента по id_col."""
        return self._elements.get(id_col)

    def get_element_db_id(self, id_col: int) -> Optional[int]:
        """Возвращает DB-ID элемента по id_col."""
        elem = self._elements.get(id_col)
        return elem.get('db_id') if elem else None

    def link_graphic_item(self, id_col: int, graphic_item: QGraphicsItem):
        """Привязывает графический элемент к id_col."""
        # ✅ FIX: Проверяем, существует ли элемент с таким id_col
        if id_col in self._elements:
            self._graphics_items[id_col] = graphic_item
            # Также сохраняем ссылку внутри элемента для быстрого доступа из графики
            self._elements[id_col]['graphic_item'] = graphic_item

    def get_graphic_item(self, id_col: int) -> Optional[QGraphicsItem]:
        """Возвращает графический элемент по id_col."""
        return self._graphics_items.get(id_col)

    def get_graphic_item_by_property_id_col(self, prop_id_col: int) -> Optional[QGraphicsItem]:
        """idCol свойства → графический виджет его элемента-владельца."""
        prop = self.get_property_by_id_col(prop_id_col)
        if prop is None:
            return None
        owner_db_id = getattr(prop, 'owner_element_id', None)
        if owner_db_id is None:
            return None
        owner_id_col = self._get_id_col_by_db_id(owner_db_id)
        if owner_id_col is None:
            return None
        return self._graphics_items.get(owner_id_col)

    def get_graphic_item_by_method_id_col(self, method_id_col: int) -> Optional[QGraphicsItem]:
        """idCol метода → графический виджет его элемента-владельца."""
        obj = self.get_object_by_id_col(method_id_col)
        if obj is None:
            return None
        owner_db_id = getattr(obj, 'owner_element_id', None)
        if owner_db_id is None:
            return None
        owner_id_col = self._get_id_col_by_db_id(owner_db_id)
        if owner_id_col is None:
            return None
        return self._graphics_items.get(owner_id_col)

    def get_graphic_item_by_signal_id_col(self, signal_id_col: int) -> Optional[QGraphicsItem]:
        """idCol сигнала → графический виджет его элемента-владельца."""
        obj = self.get_object_by_id_col(signal_id_col)
        if obj is None:
            return None
        owner_db_id = getattr(obj, 'owner_element_id', None)
        if owner_db_id is None:
            return None
        owner_id_col = self._get_id_col_by_db_id(owner_db_id)
        if owner_id_col is None:
            return None
        return self._graphics_items.get(owner_id_col)

    # =========================================================================
    # ВЫДЕЛЕНИЕ (STRICT IDCOL)
    # =========================================================================
    @property
    def selected_ids(self) -> frozenset:
        """Возвращает множество id_col выделенных элементов."""
        return frozenset(self._selected_idcols)

    @property
    def active_container_id(self) -> Optional[int]:
        """Возвращает id_col активного контейнера."""
        return self._active_container_idcol

    @property
    def last_selected_id(self) -> Optional[int]:
        """Возвращает id_col последнего выделенного элемента."""
        return self._last_selected_idcol

    def add_to_selection(self, elem_id_col: int) -> bool:
        elem = self.get_element_by_id_col(elem_id_col)
        if not elem:
            return True

        parent_db_id = elem.get('parent_id')
        parent_idcol = None
        if parent_db_id is not None:
            # Найти родителя по DB-ID сложно, если у нас нет обратного маппинга DB_ID -> id_col.
            # Поэтому будем искать родителя, перебирая элементы (медленно, но надежно для v7.3)
            # Или лучше хранить parent_id_col сразу в элементе?
            # Пока оставим поиск по DB-ID родителя, но преобразуем его в id_col.
            parent_idcol = self._get_id_col_by_db_id(parent_db_id)

        if self._selected_idcols and parent_idcol != self._active_container_idcol:
            return False

        self._selected_idcols.add(elem_id_col)
        self._active_container_idcol = parent_idcol
        self._last_selected_idcol = elem_id_col
        return True

    def remove_from_selection(self, elem_id_col: int):
        self._selected_idcols.discard(elem_id_col)
        if self._last_selected_idcol == elem_id_col:
            self._last_selected_idcol = next(iter(self._selected_idcols), None) if self._selected_idcols else None
        if not self._selected_idcols:
            self._active_container_idcol = None

    def set_selection(self, elem_id_cols: List[int], container_idcol: Optional[int]):
        self._selected_idcols.clear()
        valid = [ic for ic in elem_id_cols if self.get_element_by_id_col(ic)]
        self._selected_idcols.update(valid)
        self._active_container_idcol = container_idcol
        self._last_selected_idcol = valid[-1] if valid else None

    def clear_selection(self):
        self._selected_idcols.clear()
        self._active_container_idcol = None
        self._last_selected_idcol = None

    def select_element(self, elem_id_col: int, additive: bool = False) -> bool:
        if not self.get_element_by_id_col(elem_id_col):
            return True
        if not additive:
            self.clear_selection()
        self._selected_idcols.add(elem_id_col)

        elem = self.get_element_by_id_col(elem_id_col)
        parent_db_id = elem.get('parent_id')
        self._active_container_idcol = self._get_id_col_by_db_id(parent_db_id) if parent_db_id else None
        self._last_selected_idcol = elem_id_col
        return True

    # =========================================================================
    # СБРОС
    # =========================================================================
    def clear_all(self):
        self._elements.clear()
        self._graphics_items.clear()
        # ✅ Чистим обратный индекс
        self._db_id_to_id_col.clear()

        self._selected_idcols.clear()
        self._active_container_idcol = None
        self._last_selected_idcol = None
        self._deleted_db_ids.clear()
        self._lineages.clear()
        self._next_negative_db_id = -1
        self._next_id_col = 1
        self._idcol_to_object.clear()
        self._idcol_kind.clear()

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='collection_clear',
            element_id=0, target_id=0, target_name='*',
            old_value=0, new_value=0, source='reload', id_col=None,
        ))
    # =========================================================================
    # READ-ONLY СВОЙСТВА
    # =========================================================================
    @property
    def elements_count(self) -> int:
        return len(self._elements)

    def get_selected_elements(self) -> List[Dict]:
        """Возвращает данные выделенных элементов (по их idCol)."""
        result = []
        for idcol in self._selected_idcols:
            elem = self.get_element_by_id_col(idcol)
            if elem:
                result.append(dict(elem))
        return result

    def get_last_selected(self) -> Optional[Dict]:
        if not self._last_selected_idcol:
            return None
        elem = self.get_element_by_id_col(self._last_selected_idcol)
        return dict(elem) if elem else None

    # =========================================================================
    # БЕЗОПАСНОЕ ЧТЕНИЕ (Legacy DB-ID accessors for internal use only)
    # =========================================================================
    def get_element(self, element_id: int) -> Optional[Dict]:
        """Возвращает элемент по DB-ID. Использовать только для внутренней логики БД."""
        id_col = self._get_id_col_by_db_id(element_id)
        if id_col is None:
            return None
        return self.get_element_by_id_col(id_col)

    # =========================================================================
    # УПРАВЛЕНИЕ ЭЛЕМЕНТАМИ (DB-ID based for compatibility with old code parts)
    # =========================================================================
    def add_element(self, element_data: Dict, graphic_item: Optional[QGraphicsItem] = None) -> int:
        """Legacy method. Prefer add_element_with_metadata."""
        new_db_id = self.next_negative_db_id()
        new_id_col = self.next_id_col()

        data_copy = dict(element_data)
        data_copy['db_id'] = new_db_id
        data_copy['id'] = new_db_id
        data_copy['id_col'] = new_id_col
        data_copy['is_new'] = True
        data_copy['is_saved'] = False
        data_copy['saved_version_id'] = None
        data_copy['property_collection'] = None
        data_copy['method_collection'] = None
        data_copy['lineage'] = []
        data_copy['idVersion'] = None
        data_copy['chngID'] = None
        data_copy['chngIDVersion'] = None
        data_copy['isDelete'] = False
        data_copy['isInherited'] = False
        data_copy['isDirty'] = False

        self._elements[new_id_col] = data_copy
        # ✅ Заполняем обратный индекс O(1)
        self._db_id_to_id_col[new_db_id] = new_id_col
        self.register_idcol(data_copy, IDCOL_KIND_ELEMENT)

        if graphic_item is not None:
            self.link_graphic_item(new_id_col, graphic_item)

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='element_add',
            element_id=new_db_id,
            target_id=new_db_id,
            target_name=data_copy.get('calias', ''),
            old_value=None,
            new_value=new_id_col,
            source='user_edit',
            id_col=new_id_col,
        ))
        return new_db_id  # Returns DB-ID for legacy compatibility

    def update_element_data(self, id_col: int, data: Dict, from_graphics: bool = False):
        """Обновляет данные элемента по id_col."""
        if id_col not in self._elements:
            return
        self._elements[id_col].update(data)
        if not from_graphics:
            item = self.get_graphic_item(id_col)
            if item and hasattr(item, 'set_geometry'):
                elem = self._elements[id_col]
                item.set_geometry(
                    elem.get('x', 0), elem.get('y', 0),
                    elem.get('width', 100), elem.get('height', 30)
                )

    def remove_element(self, id_col_or_db_id: int):
        """Помечает элемент isDelete=True. Принимает id_col или db_id."""
        id_col = id_col_or_db_id
        if id_col not in self._elements:
            id_col = self._get_id_col_by_db_id(id_col_or_db_id)

        if id_col is None or id_col not in self._elements:
            return False

        elem = self._elements[id_col]
        if elem.get('isInherited', False) or elem.get('isDelete', False):
            return False

        calias = elem.get('calias', '')
        db_id = elem.get('db_id')
        idcols_to_unregister: List[int] = []

        # Собираем idCol вложенных объектов
        prop_col = elem.get('property_collection')
        if prop_col:
            for prop in prop_col.all_ordered():
                if getattr(prop, 'id_col', None):
                    idcols_to_unregister.append(prop.id_col)

        method_col = elem.get('method_collection')
        if method_col:
            for m in method_col.all_ordered():
                if getattr(m, 'id_col', None):
                    idcols_to_unregister.append(m.id_col)

        signal_items = elem.get('sub_signals') or {}
        for sig in signal_items.values():
            if getattr(sig, 'id_col', None):
                idcols_to_unregister.append(sig.id_col)

        if id_col:
            idcols_to_unregister.append(id_col)

        elem['isDelete'] = True
        self._deleted_db_ids.add(db_id)

        item = self.get_graphic_item(id_col)
        if item:
            try:
                item.setVisible(False)
            except RuntimeError:
                pass

        self.remove_from_selection(id_col)
        if self._active_container_idcol == id_col:
            self._active_container_idcol = None

        # Разрегистрация idCol вложенных и самого элемента
        for ic in idcols_to_unregister:
            self.unregister_idcol(ic)

        # ✅ Чистим обратный индекс
        if db_id is not None and db_id in self._db_id_to_id_col:
            del self._db_id_to_id_col[db_id]

        change_log.record(ChangeEvent(
            timestamp=datetime.now(), kind='element_delete',
            element_id=db_id, target_id=db_id, target_name=calias,
            old_value=db_id, new_value=None, source='user_edit', id_col=None,
        ))

        # Рекурсивное удаление детей (по DB-ID, как в публичном API)
        children_to_remove_db_ids = []
        for child_id_col, child_elem in list(self._elements.items()):
            if child_elem.get('parent_id') == db_id and not child_elem.get('isInherited', False):
                children_to_remove_db_ids.append(child_elem.get('db_id'))

        for child_db_id in children_to_remove_db_ids:
            self.remove_element(child_db_id)

        return True

    # =========================================================================
    # ПЕРЕПРИВЯЗКА
    # =========================================================================
    def reparent_element(self, db_id: int, new_parent_db_id: Optional[int]) -> bool:
        """Перепривязка по DB-ID (так как это операция БД)."""
        id_col = self._get_id_col_by_db_id(db_id)
        if id_col is None:
            return False

        elem = self._elements[id_col]
        if elem.get('isDelete', False) or elem.get('isInherited', False):
            return False

        if new_parent_db_id is not None:
            new_parent_id_col = self._get_id_col_by_db_id(new_parent_db_id)
            if new_parent_id_col is None:
                return False
            parent_elem = self._elements[new_parent_id_col]
            cclass = str(parent_elem.get('cclass', '')).lower()
            if cclass not in ('container', 'tabcontainer', 'group') or parent_elem.get('is_logical', False):
                return False
            if self._is_descendant(new_parent_db_id, db_id):
                return False

        old_parent_db_id = elem.get('parent_id')
        calias = elem.get('calias', '')
        old_x, old_y = elem.get('x', 0), elem.get('y', 0)

        if new_parent_db_id is not None:
            new_parent_id_col = self._get_id_col_by_db_id(new_parent_db_id)
            new_parent = self._elements[new_parent_id_col]
            new_local_x = old_x - new_parent.get('x', 0)
            new_local_y = old_y - new_parent.get('y', 0)
        else:
            new_local_x, new_local_y = old_x, old_y

        elem['x'], elem['y'] = new_local_x, new_local_y
        elem['parent_id'] = new_parent_db_id
        elem['is_parent_changed'] = True

        change_log.record(ChangeEvent(
            timestamp=datetime.now(), kind='element_reparent',
            element_id=db_id, target_id=db_id, target_name=calias,
            old_value=old_parent_db_id, new_value=new_parent_db_id,
            source='user_edit', id_col=id_col,
        ))

        try:
            from ide_core import goProject
            lineage = []
            node = goProject.class_registry.get_class_version(db_id)
            if node:
                order, visited, current_node = 1, set(), node
                while current_node and current_node.version_id not in visited:
                    visited.add(current_node.version_id)
                    lineage.append({
                        'order': order, 'version_id': current_node.version_id,
                        'class_name': current_node.class_name,
                        'element_id': current_node.version_id if order == 1 else None,
                        'is_own': (order == 1),
                    })
                    p_id = current_node.donor_object_id or current_node.i_base_class_version_id
                    current_node = goProject.class_registry.get_class_version(p_id) if p_id and p_id > 0 else None
                    order += 1
            self.set_lineage(db_id, lineage)
        except Exception as e:
            if isDebug: print(f"[CM.reparent] {e}")

        return True

    def _is_descendant(self, candidate_db_id: int, ancestor_db_id: int) -> bool:
        current_db_id, visited = candidate_db_id, set()
        while current_db_id is not None and current_db_id not in visited:
            visited.add(current_db_id)
            if current_db_id == ancestor_db_id: return True
            id_col = self._get_id_col_by_db_id(current_db_id)
            if id_col is None: break
            elem = self._elements.get(id_col)
            if not elem: break
            current_db_id = elem.get('parent_id')
        return False

    # =========================================================================
    # АВТОСОХРАНЕНИЕ
    # =========================================================================
    def mark_element_saved(self, id_col: int, real_version_id: int):
        if id_col in self._elements:
            self._elements[id_col]['is_saved'] = True
            self._elements[id_col]['saved_version_id'] = real_version_id
            self._elements[id_col]['chngIDVersion'] = real_version_id

    def get_saved_version_id(self, id_col_or_db_id: int) -> Optional[int]:
        id_col = id_col_or_db_id
        if id_col not in self._elements:
            id_col = self._get_id_col_by_db_id(id_col_or_db_id)
        elem = self._elements.get(id_col)
        return elem.get('saved_version_id') if elem else None

    def is_element_saved(self, id_col_or_db_id: int) -> bool:
        id_col = id_col_or_db_id
        if id_col not in self._elements:
            id_col = self._get_id_col_by_db_id(id_col_or_db_id)
        elem = self._elements.get(id_col)
        return bool(elem.get('is_saved', False)) if elem else False

    # =========================================================================
    # ГРУППОВОЕ ВЫДЕЛЕНИЕ (✅ FIX: только idCol)
    # =========================================================================
    def delete_selected(self):
        for idcol in list(self._selected_idcols):
            self.remove_element(idcol)
        self.clear_selection()

    # =========================================================================
    # ГРУППОВЫЕ ОПЕРАЦИИ
    # =========================================================================
    def move_selected(self, dx: float, dy: float):
        for idcol in list(self._selected_idcols):
            elem = self.get_element_by_id_col(idcol)
            if elem:
                db_id = elem['db_id']
                self._elements[idcol]['x'] = self._elements[idcol].get('x', 0) + dx
                self._elements[idcol]['y'] = self._elements[idcol].get('y', 0) + dy
                item = self.get_graphic_item(idcol)
                if item: item.moveBy(dx, dy)

    def resize_selected(self, dw: float, dh: float):
        for idcol in list(self._selected_idcols):
            elem = self.get_element_by_id_col(idcol)
            if elem:
                db_id = elem['db_id']
                new_w = max(20, elem.get('width', 100) + dw)
                new_h = max(15, elem.get('height', 30) + dh)
                self._elements[idcol]['width'] = new_w
                self._elements[idcol]['height'] = new_h
                item = self.get_graphic_item(idcol)
                if item and hasattr(item, 'set_rect'): item.set_rect(0, 0, new_w, new_h)

    def align_selected(self, alignment: str):
        selected = self.get_selected_elements()
        if len(selected) < 2: return
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
                idcol = e.get('id_col')
                if idcol is None: continue
                if idcol not in self._elements: continue
                elem = self._elements[idcol]
                if alignment in ('top', 'left'):
                    elem[key_map[alignment]] = ref_val
                else:
                    dim = 'height' if alignment == 'bottom' else 'width'
                    elem[key_map[alignment]] = ref_val - elem.get(dim, 0)
                item = self.get_graphic_item(idcol)
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
        if len(selected) < 2: return
        max_w = max(e.get('width', 100) for e in selected)
        for e in selected:
            idcol = e.get('id_col')
            if idcol is None: continue
            if idcol in self._elements:
                self._elements[idcol]['width'] = max_w
                item = self.get_graphic_item(idcol)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, max_w, self._elements[idcol].get('height', 30))

    def equalize_height(self):
        selected = self.get_selected_elements()
        if len(selected) < 2: return
        max_h = max(e.get('height', 30) for e in selected)
        for e in selected:
            idcol = e.get('id_col')
            if idcol is None: continue
            if idcol in self._elements:
                self._elements[idcol]['height'] = max_h
                item = self.get_graphic_item(idcol)
                if item and hasattr(item, 'set_rect'):
                    item.set_rect(0, 0, self._elements[idcol].get('width', 100), max_h)

    def equalize_sizes(self):
        last = self.get_last_selected()
        if not last: return
        ref_w, ref_h = last.get('width', 100), last.get('height', 30)
        for elem in self.get_selected_elements():
            idcol = elem.get('id_col')
            if idcol is None: continue
            db_id = elem.get('db_id')
            if db_id != last.get('db_id') and idcol in self._elements:
                self._elements[idcol]['width'] = ref_w
                self._elements[idcol]['height'] = ref_h
                item = self.get_graphic_item(idcol)
                if item and hasattr(item, 'set_rect'): item.set_rect(0, 0, ref_w, ref_h)

    # =========================================================================
    # СЕРИАЛИЗАЦИЯ
    # =========================================================================
    def get_inserts(self) -> List[Dict]:
        return [dict(v) for k, v in self._elements.items() if v.get('db_id', 0) < 0 and not v.get('is_saved', False)]

    def get_updates(self) -> List[Dict]:
        return [dict(v) for k, v in self._elements.items() if
                v.get('db_id', 0) > 0 and v.get('db_id') not in self._deleted_db_ids]

    def get_saved_new(self) -> List[Dict]:
        return [dict(v) for k, v in self._elements.items() if v.get('db_id', 0) < 0 and v.get('is_saved', False)]

    def get_deletes(self) -> List[int]:
        return list(self._deleted_db_ids)

    def get_next_id(self) -> int:
        return self.next_negative_db_id()

    # =========================================================================
    # ЛИНИЯ КРОВИ
    # =========================================================================
    def set_lineage(self, db_id: int, lineage: List[Dict]):
        id_col = self._get_id_col_by_db_id(db_id)
        if id_col and id_col in self._elements:
            self._elements[id_col]['lineage'] = lineage
            self._lineages[db_id] = lineage

    def get_lineage(self, db_id: int) -> List[Dict]:
        return self._lineages.get(db_id, [])

    # =========================================================================
    # АТОМАРНЫЙ АПДЕЙТЕР ЗНАЧЕНИЙ
    # =========================================================================
    def update_property_value_by_id_col(self, id_col: int, new_value,
                                        source: str = 'user_edit',
                                        silent: bool = False
                                        ) -> Tuple[bool, Optional[str]]:
        """
        Единая точка записи значения свойства по idCol.
        Возвращает (успех, прежнее_значение). успех=True ТОЛЬКО если модель
        реально изменилась.

        v9 FIX (адресация):
        Коллекция берётся по idCol владельца: prop.owner_element_id — это DB-ID,
        его нужно перевести через обратный индекс _get_id_col_by_db_id.
        Раньше get_property_collection(prop.owner_element_id) возвращал None,
        и апдейтер всегда отдавал (False, None) — не работали ни таблица свойств,
        ни кнопка «×», ни диалоги выбора, ни визивиг со сцены.

        v9 FIX (честный результат):
        Возвращается реальный результат col.set_value(). Если значение не
        изменилось или сеттер отказал — (False, old_value), чтобы вызывающий
        код откатил ячейку и не рисовал ложное «изменено».

        v9 FIX (источник и dirty):
        effective_silent управляет ТОЛЬКО SET-бриджем, но НЕ подменяет source.
        Внутри set_value флаг isDirty ставится по источнику: 'vizivig'/'select'/
        'user_edit'/'user_edit_reset' → ставится; 'init'/'silent'/'auto_sync' →
        нет. Раньше silent превращал любой источник в 'silent', и геометрия со
        сцены (vizivig внутри silent_mode) не попадала в сохранение.
        Явный silent=True пробрасывается в set_value как параметр — это
        осознанное подавление факта правки, отдельное от тихого режима менеджера.

        Запрет геометрии вне сцены сохранён: GEOMETRY_PROPS пишутся только
        из ALLOWED_GEOMETRY_SOURCES ('vizivig', 'init').

        SET-бридж вызывается только для пользовательских источников и только
        вне тихого режима. Для 'init'/'auto_sync'/'silent' применение к виджету —
        ответственность фазы 2 загрузки (apply_bridge_translations), иначе
        запись из виджета тут же уходит обратно в него же (рекурсия CSS/геометрии).
        """
        prop = self.get_property_by_id_col(id_col)
        if prop is None:
            return (False, None)

        # --- Запрет геометрии вне сцены ----------------------------------
        if (prop.cname in GEOMETRY_PROPS
                and source not in ALLOWED_GEOMETRY_SOURCES):
            print(f"[CM] Отказ: '{prop.cname}' нельзя менять "
                  f"source='{source}' — только со сцены (визивиг)")
            return (False, None)

        # --- STRICT IDCOL: DB-ID владельца → idCol → коллекция ------------
        owner_db_id = getattr(prop, 'owner_element_id', None)
        if owner_db_id is None:
            return (False, None)

        owner_id_col = self._get_id_col_by_db_id(owner_db_id)
        if owner_id_col is None:
            return (False, None)

        col = self.get_property_collection(owner_id_col)
        if col is None:
            return (False, None)

        old_value = prop.value

        # --- Запись в модель: источник НЕ подменяется --------------------
        changed = col.set_value(prop.cname, new_value,
                                source=source, silent=silent)
        if not changed:
            return (False, old_value)

        # --- SET-бридж: только пользовательский источник и не silent ------
        effective_silent = silent or self.is_silent()
        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if not effective_silent and source not in _NON_USER_SOURCES:
            self.apply_property_to_widget_by_id_col(id_col)

        return (True, old_value)
    def set_property_delete_by_id_col(self, id_col: int, flag: bool = True,
                                      source: str = 'user_edit') -> bool:
        """
        Единая точка установки/снятия маркера удаления свойства по idCol.

        v9 FIX (делегирование):
        Раньше метод писал isDelete/is_deleted/is_changed/isDirty напрямую
        через setattr и слал ChangeEvent с old_value=None/new_value=None
        и источником 'user_edit_delete', которого нет ни в одном контракте
        источников. Теперь вся логика — в ObjectPropertyCollection.set_property_delete:
          • атомарная запись isDelete + is_deleted (без рассинхрона);
          • isDirty для попадания в get_changed_properties() → dt_end в БД;
          • идемпотентность (повторный вызов не плодит событий);
          • extra.physical_row / defined_in_version_id / owner_version_id;
          • extra.restored=True при снятии флага;
          • id_col в ChangeEvent → точечное обновление Inspector.

        STRICT IDCOL:
        Проверка типа через get_property_by_id_col (kind == IDCOL_KIND_PROP).
        Метод/сигнал/элемент с любым idCol сюда не пройдут.
        Поиск коллекции — по prop.owner_element_id через обратный индекс
        DB-ID → idCol, без перебора _items.

        Значение value НЕ трогается: при flag=False прежняя правка
        восстанавливается как была. Очистка значения — отдельная операция «×»
        (update_property_value_by_id_col с source='user_edit_reset').

        SET-бридж не вызывается: удаление переопределения — операция модели,
        а не команда виджету. Возврат к значению предка произойдёт при
        следующей загрузке/применении коллекции.
        """
        prop = self.get_property_by_id_col(id_col)
        if prop is None:
            return False

        owner_db_id = getattr(prop, 'owner_element_id', None)
        if owner_db_id is None:
            return False

        owner_id_col = self._get_id_col_by_db_id(owner_db_id)
        if owner_id_col is None:
            return False

        col = self.get_property_collection(owner_id_col)
        if col is None:
            return False

        return col.set_property_delete(prop.cname, flag, source=source)

    def apply_property_to_widget_by_id_col(self, id_col: int) -> bool:
        from ide_core import goProject
        prop = self.get_property_by_id_col(id_col)
        if prop is None: return False
        elem_db_id = prop.owner_element_id
        id_col_elem = self._get_id_col_by_db_id(elem_db_id)
        g_item = self.get_graphic_item(id_col_elem)
        if not g_item or not getattr(g_item, 'control_widget', None):
            return False
        try:
            goProject.property_bridge_manager.apply_property_to_widget(
                g_item.control_widget, prop, version_id=elem_db_id
            )
            return True
        except Exception as e:
            if isDebug: print(f"[CM.apply_property_to_widget_by_id_col] {e}")
            return False

    # =========================================================================
    # КОЛЛЕКЦИЯ СВОЙСТВ
    # =========================================================================
    def init_property_collection(self, element_db_id: int, raw_rows: list) -> Optional[ObjectPropertyCollection]:
        id_col = self._get_id_col_by_db_id(element_db_id)
        if id_col is None or id_col not in self._elements:
            return None

        col = ObjectPropertyCollection.from_raw_rows(element_db_id, raw_rows, self)
        # v7.2: атомарная регистрация idCol
        for prop in col.all_ordered():
            prop.id_col = self.next_id_col()
            prop.owner_element_id = element_db_id
            self.register_idcol(prop, IDCOL_KIND_PROP)

        self._elements[id_col]['property_collection'] = col
        return col

    def get_property_collection(self, id_col: int) -> Optional[ObjectPropertyCollection]:
        """Возвращает коллекцию свойств элемента по id_col."""
        elem = self._elements.get(id_col)
        if elem is None:
            return None
        return elem.get('property_collection')

    def ensure_property_collection(self, id_col: int) -> Optional[ObjectPropertyCollection]:
        """Возвращает или создаёт коллекцию свойств по id_col."""
        elem = self._elements.get(id_col)
        if elem is None:
            return None
        col = elem.get('property_collection')
        if col is None:
            db_id = elem.get('db_id')
            col = ObjectPropertyCollection(db_id, self)
            elem['property_collection'] = col
        return col


    def set_property_value(self, element_db_id: int, cname: str, value: str, source: str = "manual") -> bool:
        col = self.get_property_collection(element_db_id)
        if col is None:
            return False
        return col.set_value(cname, value, source)

    def get_property_value(self, element_db_id: int, cname: str) -> Optional[str]:
        col = self.get_property_collection(element_db_id)
        if col is None:
            return None
        prop = col.get(cname)
        return prop.value if prop else None

    def apply_property_collection_to_widget(self, element_db_id: int, widget, bridge_manager) -> bool:
        col = self.get_property_collection(element_db_id)
        if col is None or widget is None:
            return False
        try:
            bridge_manager.apply_bridge_translations(widget, col, version_id=element_db_id)
            return True
        except Exception as e:
            print(f"[CollectionManager] Ошибка применения коллекции к виджету: {e}")
            return False

    def get_changed_properties(self, element_db_id: int) -> list:
        col = self.get_property_collection(element_db_id)
        if col is None:
            return []
        return col.get_changed_properties()

    def get_changed_property_meta(self, element_db_id: int) -> list:
        col = self.get_property_collection(element_db_id)
        if col is None:
            return []
        return col.get_changed_property_meta()

    def get_deleted_overrides(self, element_db_id: int) -> list:
        col = self.get_property_collection(element_db_id)
        if col is None:
            return []
        return col.get_deleted_overrides()

    # =========================================================================
    # КОЛЛЕКЦИЯ МЕТОДОВ
    # =========================================================================
    def init_method_collection(self, element_db_id: int, raw_rows: list) -> Optional[MethodCollection]:
        id_col = self._get_id_col_by_db_id(element_db_id)
        if id_col is None or id_col not in self._elements:
            return None

        col = MethodCollection.from_raw_rows(element_db_id, raw_rows, self)
        # v7.2: атомарная регистрация idCol
        for m in col.all_ordered():
            m.id_col = self.next_id_col()
            m.owner_element_id = element_db_id
            self.register_idcol(m, IDCOL_KIND_METHOD)

        self._elements[id_col]['method_collection'] = col
        return col

    def get_method_collection(self, id_col: int) -> Optional[MethodCollection]:
        """Возвращает коллекцию методов элемента по id_col."""
        elem = self._elements.get(id_col)
        if elem is None:
            return None
        return elem.get('method_collection')


    def ensure_method_collection(self, id_col: int) -> Optional[MethodCollection]:
        """Возвращает или создаёт коллекцию методов по id_col."""
        elem = self._elements.get(id_col)
        if elem is None:
            return None
        col = elem.get('method_collection')
        if col is None:
            db_id = elem.get('db_id')
            col = MethodCollection(db_id, self)
            elem['method_collection'] = col
        return col

    def get_signal_collection(self, id_col: int) -> Optional[Dict[str, SignalItem]]:
        """Возвращает коллекцию сигналов элемента (Dict[str, SignalItem]) по id_col."""
        elem = self._elements.get(id_col)
        if elem is None:
            return None
        return elem.get('sub_signals')

    def get_changed_methods(self) -> Dict[int, list]:
        result: Dict[int, list] = {}
        for id_col, elem in self._elements.items():
            col = elem.get('method_collection')
            if col is None:
                continue
            changed = col.get_changed()
            if changed:
                result[id_col] = changed
        return result

    def mark_methods_saved(self):
        for elem in self._elements.values():
            col = elem.get('method_collection')
            if col is not None:
                col.mark_saved()

    # =========================================================================
    # КОЛЛЕКЦИЯ СИГНАЛОВ
    # =========================================================================
    def init_signal_collection(self, element_db_id: int) -> None:
        """
        Конвертирует elem_data['sub_signals'] (dict {c_signal: id_method})
        в Dict[str, SignalItem] и регистрирует idCol для каждого сигнала.
        """
        id_col = self._get_id_col_by_db_id(element_db_id)
        if id_col is None or id_col not in self._elements:
            return

        elem = self._elements[id_col]
        raw_signals = elem.get('sub_signals') or {}
        # Если уже сконвертировано — выходим
        if raw_signals and all(isinstance(v, SignalItem) for v in raw_signals.values()):
            return

        new_signals: Dict[str, SignalItem] = {}
        for c_signal, id_method in raw_signals.items():
            sig = SignalItem(
                id=None,
                c_signal=str(c_signal),
                id_method=id_method,
                isInherited=True,
            )
            sig.id_col = self.next_id_col()
            sig.owner_element_id = element_db_id
            self.register_idcol(sig, IDCOL_KIND_SIGNAL)
            new_signals[c_signal] = sig

        elem['sub_signals'] = new_signals

    # =========================================================================
    # РЕГИСТРАЦИЯ IDCOL
    # =========================================================================
    def register_idcol(self, obj, kind: str) -> int:
        """Регистрирует объект в индексе idCol."""
        if isinstance(obj, dict):
            idcol = obj.get('id_col')
        else:
            idcol = getattr(obj, 'id_col', None)

        if idcol is None or idcol <= 0:
            raise ValueError(f"register_idcol: некорректный id_col ({idcol!r})")
        if idcol in self._idcol_to_object:
            raise ValueError(f"register_idcol: id_col={idcol} уже занят")

        self._idcol_to_object[idcol] = obj
        self._idcol_kind[idcol] = kind
        return idcol

    def unregister_idcol(self, id_col: int) -> None:
        """Удаляет объект из индекса idCol."""
        self._idcol_to_object.pop(id_col, None)
        self._idcol_kind.pop(id_col, None)

    # =========================================================================
    # НАВИГАЦИЯ ПО idCol
    # =========================================================================
    def get_object_by_id_col(self, id_col: int):
        return self._idcol_to_object.get(id_col)

    def get_property_by_id_col(self, id_col: int):
        if self._idcol_kind.get(id_col) != IDCOL_KIND_PROP:
            return None
        return self._idcol_to_object.get(id_col)

    def get_element_id_col_by_property_id_col(self, prop_id_col: int) -> Optional[int]:
        prop = self.get_property_by_id_col(prop_id_col)
        if prop is None:
            return None
        owner_eid = getattr(prop, 'owner_element_id', None)
        if owner_eid is None:
            return None
        # Ищем элемент по DB-ID владельца свойства
        id_col = self._get_id_col_by_db_id(owner_eid)
        if id_col is None:
            return None
        elem_data = self._elements.get(id_col)
        if elem_data is None:
            return None
        return elem_data.get('id_col')

    def get_id_col_by_element_reference(self, ref) -> Optional[int]:
        if isinstance(ref, dict):
            return ref.get('id_col')
        if isinstance(ref, int):
            # Пробуем найти как id_col, если нет - как db_id
            if ref in self._elements:
                return ref
            return self._get_id_col_by_db_id(ref)
        if hasattr(ref, 'id_col') and getattr(ref, 'id_col'):
            return ref.id_col
        if hasattr(ref, 'element_id'):
            elem_data = self._elements.get(ref.element_id)  # Это может быть db_id
            if elem_data:
                return elem_data.get('id_col')
            # Если не нашли, возможно element_id это на самом деле id_col?
            # Но по контракту element_id это DB-ID.
            return None
        return None