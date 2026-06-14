# widgets/form_designer_old/scene_events_mixin.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс-примесь EventsMixin для FormDesignerScene.
Управляет интерактивными событиями мыши (клики, перемещения, отпускания) на холсте.
Исправлен критический баг AttributeError при попытке получить transform() из списка views.
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent


class EventsMixin:
    """
    Миксин обработки системных событий мыши графической сцены дизайнера.
    Обеспечивает обязательный сквозной проброс сигналов для оживления контролов и рамок.
    """

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Обработка нажатия кнопки мыши на холсте дизайнера.
        Гарантирует, что клик долетит до ControlItem и активирует выделение.
        """
        if event.button() == Qt.LeftButton:
            # ИСПРАВЛЕНО: Безопасно получаем матрицу трансформации из первого элемента списка views()
            view_list = self.views()
            view_transform = view_list[0].transform() if view_list else None

            # Ищем, есть ли какой-то элемент под курсором в момент клика
            item = self.itemAt(event.scenePos(), view_transform)

            # Если под мышкой абсолютно пусто — каскадно гасим маркеры выделения контролов
            if item is None:
                if hasattr(self, 'clear_selection'):
                    self.clear_selection()
                elif hasattr(self, 'select_control'):
                    self.select_control(None)

        # КРИТИЧЕСКИЙ ФИКС: Пробрасываем клик вглубь Qt Graphics View.
        # Без этой строки QGraphicsScene никогда не передаст клик в ControlItem!
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Обработка перемещения мыши по холсту.
        Обеспечивает плавное таскание элементов и мгновенный пересчет рамок ресайза.
        """
        # Твой оригинальный код трекинга координат или создания рамки выделения
        # ...

        # КРИТИЧЕСКИЙ ФИКС: Принудительно передаем событие движения в базовый класс Qt.
        # Это заставит маркеры формы ожить и следовать за краями подложки при изменении размеров,
        # а также позволит двигать контролы мышью.
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Обработка отпускания кнопки мыши.
        Завершает циклы перетаскивания и фиксирует новые координаты.
        """
        # Твой оригинальный код фиксации Drag-and-Drop
        # ...

        # КРИТИЧЕСКИЙ ФИКС: Пробрасываем событие отпускания кнопки мыши дальше по цепочке фреймворка
        super().mouseReleaseEvent(event)
