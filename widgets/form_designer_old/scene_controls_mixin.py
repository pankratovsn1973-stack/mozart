# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_controls_mixin.py
# -*- coding: utf-8 -*-

"""
Модуль: Миксин управления контролами на сцене дизайнера.

Роль в архитектуре Mozart ERP:
    - Добавление, удаление и управление контролами на графической сцене.
    - Обеспечивает сбор данных для сохранения (Unit of Work).
    - Интегрируется с FormObjectsRegistry для метаданных и DesignerDataModel для свойств.
    - Поддерживает как корневые контролы, так и дочерние элементы (internal controls).
    - Реализует генерацию отрицательных ID для новых контролов (пункт 3.1.1.1).

Ключевые зависимости:
    - FormObjectsRegistry - для регистрации и поиска контролов.
    - DesignerDataModel - для хранения свойств контролов.
    - ControlItem - графическое представление контрола на сцене.
"""

from PySide6.QtCore import Qt, QPointF
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class ControlsMixin:
    """
    Миксин сцены: добавление, удаление, выделение контролов, сохранение данных.

    Назначение:
        - Управление жизненным циклом контролов на сцене.
        - Интеграция с реестром объектов для метаданных.
        - Сбор данных для сохранения в БД.
        - Генерация отрицательных ID для новых контролов.

    Ключевые свойства:
        - controls: dict[str, ControlItem] - Словарь всех контролов на сцене (ключ = control_id).
        - selected_control: ControlItem - Текущий выделенный контрол.
        - _next_negative_id: int - Счетчик для генерации отрицательных ID.

    Основные методы:
        - add_control() - Добавляет новый контрол на сцену.
        - delete_control() - Удаляет контрол со сцены и из реестра.
        - get_controls_data() - Собирает данные всех контролов для сохранения.
        - clear_controls() - Удаляет все контролы со сцены.
        - _generate_negative_id() - Генерирует следующий отрицательный ID.
    """

    def _init_controls(self):
        """Инициализация структур для управления контролами."""
        self.controls = {}
        self.selected_control = None
        self._next_negative_id = -1  # Счетчик для генерации отрицательных ID

    # ==================== ПУНКТ 3.1.1.1 ====================
    def _generate_negative_id(self):
        """
        Генерация следующего отрицательного ID для новых контролов.

        Returns:
            str - Отрицательный ID (например, "-1", "-2")

        Примечание:
            Использует счетчик _next_negative_id, который уменьшается
            при каждом вызове, гарантируя уникальность ID в пределах сессии.
        """
        current_id = self._next_negative_id
        self._next_negative_id -= 1
        return str(current_id)

    # ==================== ПУНКТ 2.1.2.1 ====================
    def add_control(self, control_widget, control_id=None, control_type=None,
                    x=50, y=50, parent_item=None, calias="", full_path=""):
        """
        Добавление контрола на сцену с регистрацией в реестре.

        Args:
            control_widget: QWidget - Виджет контрола
            control_id: str - ID из БД (если None - генерируется отрицательный)
            control_type: str - Тип контрола (textbox, reference, etc.)
            x: float - Координата X на сцене
            y: float - Координата Y на сцене
            parent_item: ControlItem - Родительский контрол (для иерархии)
            calias: str - Бизнес-алиас контрола
            full_path: str - Полный путь в иерархии

        Returns:
            ControlItem or None - Созданный графический объект
        """
        from .control_item import ControlItem

        # ==================== ПУНКТ 3.1.1.1 ====================
        # Если control_id не передан - генерируем отрицательный
        if control_id is None:
            control_id = self._generate_negative_id()

        control_id = str(control_id)

        # Если control_type не указан, пытаемся определить из виджета
        if control_type is None:
            control_type = control_widget.__class__.__name__.lower()
            if control_type == "qlineedit":
                control_type = "textbox"
            elif control_type == "qlabel":
                control_type = "label"
            elif control_type == "qpushbutton":
                control_type = "button"

        # ==================== ПУНКТ 6.1.2.1 ====================
        # Вычисляем parentid из родительского контрола
        parentid = None
        if parent_item:
            if hasattr(parent_item, 'control_id'):
                parentid = str(parent_item.control_id)
            elif hasattr(parent_item, 'objectName'):
                # Fallback для случаев, когда parent_item - это виджет, а не ControlItem
                registry = FormObjectsRegistry()
                parentid = registry.get_id_by_widget(parent_item)
                if parentid == "unknown":
                    parentid = None

        try:
            x, y = float(x or 50.0), float(y or 50.0)
        except (ValueError, TypeError):
            x, y = 50.0, 50.0

        # Создаем графический объект
        actual_parent = parent_item if parent_item else self.background
        item = ControlItem(control_widget, control_id, control_type, parent=actual_parent)
        item.setPos(QPointF(x, y))

        # ==================== ПУНКТ 2.1.1.2 ====================
        # Регистрация в реестре с control_id как ключом
        registry = FormObjectsRegistry()
        registry.register_object(
            control_id=control_id,
            widget_obj=item,
            parentid=parentid,
            full_path=full_path,
            calias=calias,
            cclass=control_type
        )

        # Подключаем сигналы
        item.selected_changed.connect(lambda sel: self._on_control_selected(item, sel))
        item.geometry_changed.connect(self._on_control_geometry_changed)

        # Сохраняем в словарь контролов
        self.controls[control_id] = item

        # Переключаем виджет в режим дизайна, если поддерживается
        if hasattr(control_widget, 'set_design_mode'):
            control_widget.set_design_mode(True)

        # Сигнал о добавлении контрола
        if hasattr(self, 'control_added'):
            self.control_added.emit(item)

        return item

    def _on_control_selected(self, control_item, selected):
        """Обработка изменения состояния выделения контрола."""
        if selected and control_item:
            self.selected_control = control_item
            if hasattr(self, 'set_focused_control'):
                self.set_focused_control(control_item)
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(control_item)
        else:
            if len(self.selectedItems()) == 0:
                self.selected_control = None
                if hasattr(self, 'set_focused_control'):
                    self.set_focused_control(None)
                if hasattr(self, 'control_selected'):
                    self.control_selected.emit(None)

    def _on_control_geometry_changed(self, control_id, x, y, width, height):
        """Обработка изменения геометрии контрола."""
        if hasattr(self, 'geometry_changed'):
            self.geometry_changed.emit(str(control_id), int(x), int(y), int(width), int(height))

    def delete_control(self, control_id):
        """
        Удаление контрола со сцены и из реестра.

        Args:
            control_id: str - ID контрола для удаления
        """
        cid_str = str(control_id).strip()
        if cid_str not in self.controls:
            return

        item = self.controls[cid_str]
        if self.selected_control == item:
            self.selected_control = None
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

        # Удаляем со сцены
        if item and item.scene() == self:
            self.removeItem(item)

        # Удаляем из словаря контролов
        del self.controls[cid_str]

        # Помечаем на удаление в Unit of Work
        if hasattr(self, 'deleted_control_ids'):
            self.deleted_control_ids.add(cid_str)

        # Удаляем из реестра
        registry = FormObjectsRegistry()
        if cid_str in registry._registry:
            # Проверяем, есть ли дочерние элементы
            children_to_delete = []
            for cid, meta in registry._registry.items():
                if meta.get("parentid") == cid_str:
                    children_to_delete.append(cid)

            # Удаляем дочерние элементы
            for child_id in children_to_delete:
                # Удаляем из индекса
                child_meta = registry._registry.get(child_id)
                if child_meta:
                    path_key = (child_meta.get("parentid"), child_meta.get("calias"))
                    if path_key in registry._index_by_path:
                        del registry._index_by_path[path_key]
                    # Удаляем из wid_to_cid_map
                    ref = child_meta.get("widget_ref")
                    if ref:
                        actual_ref = ref() if isinstance(ref, weakref.ref) else ref
                        if actual_ref:
                            wid = id(actual_ref)
                            if wid in registry._wid_to_cid_map:
                                del registry._wid_to_cid_map[wid]
                # Удаляем из _registry
                del registry._registry[child_id]

            # Удаляем сам контрол
            del registry._registry[cid_str]
            # Удаляем из wid_to_cid_map
            for wid, stored_cid in list(registry._wid_to_cid_map.items()):
                if stored_cid == cid_str:
                    del registry._wid_to_cid_map[wid]
            # Удаляем из индекса
            for path_key, stored_cid in list(registry._index_by_path.items()):
                if stored_cid == cid_str:
                    del registry._index_by_path[path_key]

        # Сигнал об удалении
        if hasattr(self, 'control_deleted'):
            self.control_deleted.emit(cid_str)

    # ==================== ПУНКТ 4.1.2.1 ====================
    def get_controls_data(self) -> list:
        """
        Сбор данных всех контролов для сохранения (READ-ONLY).

        Важно: НЕ вызывает registry.register_object внутри метода!
        Сбор данных идет простым перебором _registry.values().
        Если у подконтрола отрицательный ID — он попадет в INSERT.
        Если положительный — в UPDATE.

        Returns:
            list - Список словарей с данными контролов
        """
        controls_list = []
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        # Системные классы, которые не должны сохраняться
        system_garbage_classes = ('formbackground', 'resizehandle', 'formbackgroundsignals')
        system_garbage_ids = ('form_root', '1', '840')

        # Получаем ID формы для родительских связей
        form_id = "841"
        if hasattr(self, 'background') and self.background:
            form_id = registry.get_id_by_widget(self.background)
            if form_id == "unknown":
                form_id = "841"

        # Перебираем все объекты в реестре
        for control_id, meta in registry._registry.items():
            # Пропускаем системные объекты
            if control_id in system_garbage_ids:
                continue

            widget_ref = meta.get("widget_ref")
            if not widget_ref:
                continue

            widget_obj = widget_ref() if isinstance(widget_ref, weakref.ref) else widget_ref
            if not widget_obj:
                continue

            # Проверяем видимость
            if hasattr(widget_obj, 'isVisible') and not widget_obj.isVisible():
                continue

            # Получаем данные из метаданных
            calias = meta.get("calias", "")
            cclass = meta.get("cclass", "")
            parentid = meta.get("parentid")

            # Получаем геометрию
            if hasattr(widget_obj, 'rect') and hasattr(widget_obj, 'pos'):
                pos, rect = widget_obj.pos(), widget_obj.rect()
                x, y = int(pos.x()), int(pos.y())
                width, height = int(rect.width()), int(rect.height())
            elif hasattr(widget_obj, 'geometry'):
                geo = widget_obj.geometry()
                x, y = geo.x(), geo.y()
                width, height = geo.width(), geo.height()
            else:
                x, y, width, height = 50, 50, 150, 30

            # Собираем свойства
            props = {
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }

            # Добавляем дополнительные свойства из модели
            prop_names = ['label', 'binding_field', 'entity_alias', 'display_field',
                          'selector_form', 'is_required', 'is_readonly']
            for prop_name in prop_names:
                val = model.get_value(control_id, prop_name)
                if val:
                    props[prop_name] = val

            # Определяем родителя для сохранения
            resolved_parent = str(parentid) if parentid else str(form_id)

            # Добавляем в список
            controls_list.append({
                'id': control_id,
                'parentid': resolved_parent,
                'calias': calias,
                'cclass': cclass,
                'properties': props
            })

        return controls_list

    def clear_controls(self):
        """Удаляет все контролы со сцены."""
        control_ids = list(self.controls.keys())
        for cid in control_ids:
            self.delete_control(cid)
        self.controls.clear()
        self.selected_control = None
        self._next_negative_id = -1  # Сбрасываем счетчик