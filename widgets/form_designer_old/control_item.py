# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item.py
# -*- coding: utf-8 -*-

"""
Модуль: Главный управляющий класс графического прокси-контейнера.

Роль в архитектуре Mozart ERP:
    - Представляет контрол на сцене визуального дизайнера.
    - Инкапсулирует все взаимодействия с пользователем:
        * Выделение и фокус
        * Отрисовка рамки выделения (синий пунктир)
        * Управление маркерами изменения размеров (ResizeHandle)
        * Обработка каскадных кликов по внутренним элементам (Reference)
        * Перетаскивание (делегируется ControlItemMovement)
        * Контекстное меню (делегируется ControlItemContext)
    - Идентификация строго через control_id из БД.
    - Интеграция с FormObjectsRegistry и DesignerDataModel.

Ключевые зависимости:
    - ControlItemMovement - миксин перетаскивания.
    - ControlItemContext - миксин контекстного меню.
    - FormObjectsRegistry - реестр метаданных.
    - ResizeHandle - маркер изменения размеров.
    - FocusRegistry - управление фокусом.

Принципы:
    - Единый источник истины для выделения.
    - Централизованная обработка всех событий мыши.
    - Четкое разделение ответственности с миксинами.
"""

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QGraphicsProxyWidget, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainter

from .control_item_movement import ControlItemMovement
from .control_item_context import ControlItemContext
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry
from .focus_registry import FocusRegistry


class ControlItem(ControlItemMovement, ControlItemContext, ControlItemBase):
    """
    Главный управляющий класс графического прокси-контейнера на сцене.

    Назначение:
        - Проксирование Qt-виджетов на графическую сцену.
        - Обработка всех событий мыши и клавиатуры.
        - Управление состоянием выделения и фокуса.
        - Отрисовка фирменной синей пунктирной рамки.
        - Управление маркером изменения размеров (ResizeHandle).
        - Каскадная обработка кликов по внутренним элементам референсов.

    Ключевые свойства:
        - control_id: str - Уникальный ID из БД (или отрицательный для новых).
        - control_type: str - Тип контрола (textbox, reference, button, etc.).
        - _selected_child_widgets: list - Маркеры изменения размеров.
        - _active_child_item: QWidget - Активный внутренний элемент (для референсов).
        - _focused_child_widget: QWidget - Сфокусированный внутренний элемент.

    Сигналы:
        - selected_changed(bool) - Изменение состояния выделения.
        - geometry_changed(str, int, int, int, int) - Изменение геометрии.
    """

    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        """
        Инициализация контрола на сцене.

        Args:
            widget: QWidget - Виджет для проксирования
            control_id: str - ID из БД (или отрицательный для новых)
            control_type: str - Тип контрола
            parent: QGraphicsItem - Родительский графический элемент
        """
        # ==================== ПУНКТ 5.1.3 ====================
        # Инициализация миксинов в правильном порядке
        ControlItemMovement.__init__(self, widget, control_id, control_type, parent)
        ControlItemContext.__init__(self)  # Пустой инициализатор
        ControlItemBase.__init__(self, widget, control_id, control_type, parent)

        # Состояние контрола
        self.control_id = str(control_id).strip()
        self.control_type = str(control_type).lower()

        # Внутренние элементы (для составных контролов)
        self._selected_child_widgets = []
        self._active_child_item = None
        self._focused_child_widget = None

        # Настройка графического объекта
        self.setWidget(widget)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)

    # ==================== ПУНКТ 5.1.3.1 ====================
    def paint(self, painter: QPainter, option, widget):
        """
        Переопределение отрисовки: наложение синей пунктирной рамки выделения.

        ВАЖНО: Этот метод переопределяет paint из ControlItemBase.
        Используется фирменный стиль FoxPro: синий пунктир толщиной 1.5px.

        Args:
            painter: QPainter - Художник для отрисовки
            option: QStyleOptionGraphicsItem - Опции стиля
            widget: QWidget - Виджет для отрисовки
        """
        # Вызываем базовую отрисовку Qt-виджета
        super().paint(painter, option, widget)

        # Рисуем рамку фокуса только если элемент выбран
        if self.isSelected():
            painter.save()

            # Настройка пера: синий пунктир толщиной 1.5 пикселя
            pen = QPen(QColor(0, 120, 215), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Рисуем контур строго по внешним границам геометрии
            rect = self.rect()
            painter.drawRect(rect)

            painter.restore()

    # ==================== ПУНКТ 5.1.3.2 ====================
    def update_handles_position(self):
        """
        Синхронизация положения маркера ресайза (юго-восточный угол).

        Поддерживает два режима:
        1. Форма - маркер в правом нижнем углу формы.
        2. Контрол - маркер в правом нижнем углу контрола.
        3. Внутренний элемент - маркер привязан к активному дочернему виджету.
        """
        # Проверяем, что контрол выделен и находится в фокусе
        if not self.isSelected():
            self.clear_internal_selection()
            return

        if self.scene() and self.scene().focused_control != self:
            self.clear_internal_selection()
            return

        # Инициализируем список маркеров, если его нет
        if not hasattr(self, '_selected_child_widgets') or self._selected_child_widgets is None:
            self._selected_child_widgets = []

        # Создаем маркер, если его еще нет
        if not self._selected_child_widgets and self.scene():
            try:
                from .resize_handle import ResizeHandle
                # ==================== ПУНКТ 5.1.3.2 ====================
                # ИСПРАВЛЕНО: Передаем 4 (позиция BottomRight) и self как target
                handle = ResizeHandle(4, self, parent=None)
                self.scene().addItem(handle)
                handle.setZValue(self.zValue() + 1000)
                self._selected_child_widgets.append(handle)
            except Exception as e:
                print(f"[HANDLE_LOG] Ошибка создания ResizeHandle: {e}")

        # Обновляем позицию маркера
        for handle in self._selected_child_widgets:
            try:
                handle.update_position()
                handle.setVisible(True)
                if hasattr(handle, 'update'):
                    handle.update()
            except Exception as e:
                print(f"[HANDLE_LOG] Ошибка позиционирования хэндла: {e}")

    # ==================== ПУНКТ 5.1.3.3 ====================
    def clear_internal_selection(self):
        """
        Сброс и скрытие маркеров изменения размеров.

        Удаляет все маркеры со сцены и сбрасывает состояние внутреннего выделения.
        """
        if hasattr(self, '_selected_child_widgets') and self._selected_child_widgets:
            for handle in list(self._selected_child_widgets):
                if hasattr(handle, 'setVisible'):
                    handle.setVisible(False)
                if handle.scene():
                    try:
                        handle.scene().removeItem(handle)
                    except RuntimeError:
                        pass
            self._selected_child_widgets.clear()

        if self._active_child_item is not None or self._focused_child_widget is not None:
            self._active_child_item = None
            self._focused_child_widget = None

        self.update()

    # ==================== ПУНКТ 5.1.3.3 ====================
    def handle_internal_click(self, event):
        """
        Активация контекста внутренней части составного референса при каскадном клике.

        Args:
            event: QGraphicsSceneMouseEvent - Событие мыши
        """
        if not self.scene():
            return

        source_widget = self.widget()
        if not source_widget:
            return

        # Находим физический элемент под курсором мыши
        child = source_widget.childAt(event.pos().toPoint())
        if not child and event.widget():
            child = event.widget()

        if child and child != source_widget:
            # Получаем calias дочернего элемента
            child_calias = getattr(child, 'calias', child.objectName())

            # Проверяем, является ли это внутренним элементом референса
            internal_aliases = ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref')
            if child_calias in internal_aliases:
                # ==================== ПУНКТ 5.1.3.3 ====================
                # ИСПРАВЛЕНО: Используем get_meta_by_parent_and_calias
                registry = FormObjectsRegistry()
                child_meta = registry.get_meta_by_parent_and_calias(
                    self.control_id,  # parentid
                    child_calias  # calias
                )

                if child_meta:
                    print(f"[OK] Метаданные найдены по пути: Parent={self.control_id}, Calias={child_calias}")
                    # Фиксируем активный дочерний контекст
                    self.scene()._active_context_container = self
                    self._active_child_item = child
                    self._focused_child_widget = child

                    # Обновляем маркер
                    self.update_handles_position()
                    self.update()
                    event.accept()
                    return
                else:
                    print(f"[FAIL] Метаданные НЕ найдены для Parent={self.control_id}, Calias={child_calias}")

    # ==================== ПУНКТ 5.1.3 ====================
    # МЕТОДЫ ОБРАБОТКИ СОБЫТИЙ (ЦЕНТРАЛИЗОВАННАЯ ЛОГИКА)
    # ==================== ПУНКТ 5.1.3 ====================

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Централизованная обработка нажатия мыши.

        Определяет тип клика и делегирует соответствующим методам:
        1. Правый клик -> контекстное меню
        2. Клик по маркеру -> ресайз (обрабатывается в ResizeHandle)
        3. Клик по внутреннему элементу -> каскадная активация
        4. Обычный клик -> выделение контрола
        """
        scene = self.scene()
        if not scene:
            return super().mousePressEvent(event)

        # ==================== ПУНКТ 5.1.3 ====================
        # 1. ПРАВЫЙ КЛИК -> КОНТЕКСТНОЕ МЕНЮ
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 2. Проверка клика по маркеру ресайза
            for handle in getattr(self, '_selected_child_widgets', []):
                if handle.isVisible():
                    local_pos = handle.mapFromScene(event.scenePos())
                    if handle.contains(local_pos):
                        # Маркер обрабатывает клик самостоятельно
                        return

            # 3. ПРОВЕРКА ВНУТРЕННЕГО ЭЛЕМЕНТА (КАСКАДНЫЙ КЛИК)
            is_internal_child = False
            registry = FormObjectsRegistry()
            meta = registry.get_meta_by_widget(self)

            if meta:
                parent_id = meta.get('parentid')
                is_internal_child = bool(
                    parent_id and
                    str(parent_id).strip() not in ('', 'None', 'form_root')
                )

            # Если контрол не в коллекции выделения - делаем полный сброс
            if self not in scene.selectedItems():
                if not is_internal_child:
                    # Корневой контрол -> полный сброс и выделение
                    if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                        scene.clearSelection()
                        FocusRegistry().reset_active_context()

                    self._active_child_item = None
                    self._focused_child_widget = None
                    self.clear_internal_selection()

                    self.setSelected(True)
                    scene.set_focused_control(self)
                    self.update()
                    self.update_handles_position()
                    event.accept()
                    return

            # 4. КАСКАДНЫЙ КЛИК ПО ВНУТРЕННЕМУ ЭЛЕМЕНТУ
            source_widget = self.widget()
            if source_widget:
                child = source_widget.childAt(event.pos().toPoint())
                if not child and event.widget():
                    child = event.widget()

                if child and child != source_widget:
                    child_calias = getattr(child, 'calias', child.objectName())
                    internal_aliases = ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref')

                    if child_calias in internal_aliases:
                        self.handle_internal_click(event)
                        event.accept()
                        return

            # 5. ОБЫЧНЫЙ ДРАГ (только для корневых контролов)
            if not is_internal_child:
                event.accept()
                ControlItemMovement.mousePressEvent(self, event)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Делегирование движения миксину перетаскивания.
        """
        if self._is_dragging:
            ControlItemMovement.mouseMoveEvent(self, event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Делегирование завершения движения миксину перетаскивания.
        """
        if self._is_dragging:
            ControlItemMovement.mouseReleaseEvent(self, event)
        else:
            super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """
        Автоматическая очистка маркеров при снятии нативного выделения Qt.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            is_selected = bool(value)
            if not is_selected:
                self.clear_internal_selection()
        return super().itemChange(change, value)

    def setWidgetSize(self, width: float, height: float):
        """
        Изменяет размер контрола через нативный механизм QGraphicsProxyWidget.

        Args:
            width: float - Новая ширина
            height: float - Новая высота
        """
        w = max(20.0, float(width))
        h = max(15.0, float(height))

        self.setGeometry(self.pos().x(), self.pos().y(), w, h)

        widget = self.widget()
        if widget:
            widget.setFixedSize(int(w), int(h))
            if hasattr(widget, 'updateGeometry'):
                widget.updateGeometry()
            if hasattr(widget, 'update'):
                widget.update()

        self.update_handles_position()
        self.geometry_changed.emit(
            self.control_id,
            int(self.pos().x()),
            int(self.pos().y()),
            int(w),
            int(h)
        )
        if self.scene():
            self.scene().update()

    def _get_calias(self, widget):
        """
        Безопасное получение calias у виджета.

        Args:
            widget: QWidget - Виджет для получения calias

        Returns:
            str - calias или пустая строка
        """
        if hasattr(widget, 'calias'):
            calias = getattr(widget, 'calias', None)
            if calias:
                return str(calias).strip()

        # Fallback: используем objectName
        obj_name = widget.objectName()
        if obj_name:
            # Обрезаем суффикс с ID, если есть
            internal_aliases = ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref')
            for alias in internal_aliases:
                if obj_name.startswith(alias):
                    return alias
            return obj_name

        return ""