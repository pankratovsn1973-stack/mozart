# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_dragdrop_mixin.py
# -*- coding: utf-8 -*-

"""
Модуль: Миксин перетаскивания контролов из палитры на сцену.

Роль в архитектуре Mozart ERP:
    - Обеспечивает Drag & Drop функциональность для добавления новых контролов.
    - Создает новые контролы из палитры с отрицательными ID (маркер INSERT).
    - Правильно вычисляет parentid для новых контролов.
    - Интегрируется с FormObjectsRegistry и ControlsMixin.

Ключевые зависимости:
    - controls.create_control - фабрика создания контролов.
    - FormObjectsRegistry - для регистрации контролов.
    - ControlsMixin.add_control - для добавления на сцену.

Принципы:
    - Новые контролы получают отрицательные ID (пункт 3.1.1.1).
    - Правильное вычисление parentid на основе позиции на сцене.
    - Привязка к сетке (snap) для точного позиционирования.
"""

import uuid
from PySide6.QtCore import QPointF
from .form_objects_registry import FormObjectsRegistry


class DragDropMixin:
    """
    Миксин: перетаскивание контролов из палитры на сцену.

    Назначение:
        - Обработка событий drag & drop.
        - Создание новых контролов из палитры.
        - Генерация отрицательных ID для новых контролов.
        - Правильное позиционирование с учетом привязки к сетке.

    Ключевые свойства:
        - Использует ControlsMixin._generate_negative_id() для ID.
        - Использует ControlsMixin.add_control() для добавления.

    Методы:
        - dragEnterEvent() - Проверка возможности перетаскивания.
        - dragMoveEvent() - Обновление позиции при перетаскивании.
        - dropEvent() - Создание контрола из палитры.
        - _calculate_parentid() - Вычисление родителя по позиции.
    """

    # ==================== ПУНКТ 6.1.3.1 ====================
    def _calculate_parentid(self, scene_pos: QPointF) -> str:
        """
        Вычисляет parentid для нового контрола на основе позиции на сцене.

        Логика:
        1. Если позиция попадает на существующий контрол - используем его ID как parentid.
        2. Если позиция попадает на бланк формы - parentid = None (корневой).
        3. Если позиция вне формы - parentid = None.

        Args:
            scene_pos: QPointF - Позиция на сцене

        Returns:
            str or None - ID родительского контрола или None
        """
        registry = FormObjectsRegistry()

        # Проверяем, есть ли контрол под курсором
        item = self.itemAt(scene_pos, self.views()[0].transform() if self.views() else None)

        if item:
            # Проверяем, является ли это контролом
            if hasattr(item, 'control_id'):
                parent_id = item.control_id
                # Проверяем, что это не системный контрол
                if parent_id not in ('1', '840', 'form_root'):
                    return str(parent_id)

            # Проверяем, не является ли это бланком формы
            if hasattr(item, 'parentItem') and item.parentItem():
                parent = item.parentItem()
                if hasattr(parent, 'control_id'):
                    return str(parent.control_id)

        # Если под курсором ничего нет, проверяем, внутри ли формы
        if self.background:
            form_pos = self.background.mapFromScene(scene_pos)
            if 0 <= form_pos.x() <= self.background.width and 0 <= form_pos.y() <= self.background.height:
                # Внутри формы, но не на контроле -> корневой
                return None

        # Вне формы -> корневой
        return None

    # ==================== ПУНКТ 6.1.3.2 ====================
    def dragEnterEvent(self, event):
        """
        Проверка возможности перетаскивания.

        Args:
            event: QGraphicsSceneDragDropEvent - Событие перетаскивания
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    # ==================== ПУНКТ 6.1.3.3 ====================
    def dragMoveEvent(self, event):
        """
        Обновление позиции при перетаскивании.

        Args:
            event: QGraphicsSceneDragDropEvent - Событие перетаскивания
        """
        event.acceptProposedAction()

    # ==================== ПУНКТ 6.1.3.4 ====================
    def dropEvent(self, event):
        """
        Создание контрола из палитры при сбросе.

        Args:
            event: QGraphicsSceneDragDropEvent - Событие сброса
        """
        if not self.background:
            event.ignore()
            return

        control_type = event.mimeData().text()
        if not control_type:
            event.ignore()
            return

        # Получаем позицию на сцене
        scene_pos = event.scenePosition()

        # ==================== ПУНКТ 6.1.3.4 ====================
        # Привязка к сетке (если включена)
        if self._snap_enabled:
            scene_pos = self.snap_to_grid(scene_pos)

        # Преобразуем в координаты формы
        form_pos = self.background.mapFromScene(scene_pos)
        x = form_pos.x()
        y = form_pos.y()

        # Ограничения позиции внутри формы
        w_default = 150
        h_default = 30
        max_x = self.background.width - w_default
        max_y = self.background.height - 30
        x = max(0, min(x, max_x))
        y = max(30, min(y, max_y))

        # ==================== ПУНКТ 6.1.3.4 ====================
        # Вычисляем parentid на основе позиции
        parentid = self._calculate_parentid(scene_pos)

        # Получаем родительский элемент (если parentid указан)
        parent_item = None
        if parentid:
            registry = FormObjectsRegistry()
            # Ищем родительский элемент на сцене
            for cid, item in self.controls.items():
                if cid == parentid:
                    parent_item = item
                    break

        # ==================== ПУНКТ 3.1.1.1 ====================
        # Генерируем отрицательный ID для нового контрола
        control_id = self._generate_negative_id()

        # Создаем виджет контрола
        from controls import create_control
        widget = create_control(control_type, parent=None, db=self.db)

        if widget:
            # Устанавливаем атрибуты
            widget.setObjectName(f"{control_type}_{control_id}")

            # ==================== ПУНКТ 6.1.3.4 ====================
            # Добавляем контрол на сцену с правильным parentid
            self.add_control(
                control_widget=widget,
                control_id=control_id,
                control_type=control_type,
                x=x,
                y=y,
                parent_item=parent_item,
                calias=f"{control_type}_{control_id}",
                full_path=self._build_path_for_new_control(parentid, control_type, control_id)
            )

            # Выделяем новый контрол
            self.clear_selection()
            if control_id in self.controls:
                self.controls[control_id].setSelected(True)
                self.set_focused_control(self.controls[control_id])

            event.acceptProposedAction()
        else:
            event.ignore()

    # ==================== ПУНКТ 6.1.3.5 ====================
    def _build_path_for_new_control(self, parentid: str, control_type: str, control_id: str) -> str:
        """
        Строит полный путь для нового контрола.

        Args:
            parentid: str - ID родительского контрола
            control_type: str - Тип контрола
            control_id: str - ID нового контрола

        Returns:
            str - Полный путь в иерархии
        """
        if not parentid:
            return f"{control_type}_{control_id}"

        registry = FormObjectsRegistry()
        parent_meta = registry.get_meta_by_id(parentid)

        if parent_meta:
            parent_path = parent_meta.get('full_path', '')
            if parent_path:
                return f"{parent_path}.{control_type}_{control_id}"
            else:
                parent_alias = parent_meta.get('calias', '')
                if parent_alias:
                    return f"{parent_alias}.{control_type}_{control_id}"

        return f"{control_type}_{control_id}"

    # ==================== ПУНКТ 6.1.3.6 ====================
    def _get_control_at_position(self, scene_pos: QPointF):
        """
        Возвращает контрол в указанной позиции.

        Args:
            scene_pos: QPointF - Позиция на сцене

        Returns:
            ControlItem or None - Контрол или None
        """
        item = self.itemAt(scene_pos, self.views()[0].transform() if self.views() else None)
        if item:
            if hasattr(item, 'control_id'):
                return item
            if hasattr(item, 'parentItem') and hasattr(item.parentItem(), 'control_id'):
                return item.parentItem()
        return None

    # ==================== ПУНКТ 6.1.3.7 ====================
    def _is_valid_drop_target(self, scene_pos: QPointF) -> bool:
        """
        Проверяет, можно ли сбросить контрол в указанную позицию.

        Args:
            scene_pos: QPointF - Позиция на сцене

        Returns:
            bool - True если можно сбросить
        """
        if not self.background:
            return False

        form_pos = self.background.mapFromScene(scene_pos)
        return (0 <= form_pos.x() <= self.background.width and
                0 <= form_pos.y() <= self.background.height)