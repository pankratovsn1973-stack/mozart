# widgets/form_designer_old/scene_events_mixin.py
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from .control_item import ControlItem
from .resize_handle import ResizeHandle


class EventsMixin:
    """
    Миксин обработки системных событий мыши графической сцены дизайнера.
    Обеспечивает обязательный сквозной проброс сигналов для оживления контролов и рамок.
    """

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Обработка нажатия кнопки мыши на холсте дизайнера.
        Управляет одиночным/множественным выделением контролов и сбросом фокуса на форму.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            view_list = self.views()
            view_transform = view_list[0].transform() if view_list else None

            # Ищем графический элемент под курсором в момент клика
            item = self.itemAt(event.scenePos(), view_transform)

            # Если кликнули на пустое место, на саму форму или её элементы (заголовок/статусбар)
            if item is None or item == self.background or item == getattr(self.background, 'title_bar',
                                                                          None) or item == getattr(self.background,
                                                                                                   'status_bar', None):
                # Снимаем выделение со всех выбранных контролов холста
                self.clearSelection()
                # Переключаем инспектор свойств PropertyEditor обратно на параметры формы
                if hasattr(self, 'select_control'):
                    self.select_control(None)

                # Пробрасываем клик дальше, чтобы TitleBarStub мог начать drag формы
                super().mousePressEvent(event)
                return

            # Клик пришелся по контролу (ControlItem)
            # Если зажат Ctrl — инвертируем статус выделения этого элемента, не трогая остальные
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if isinstance(item, ControlItem):
                    item.setSelected(not item.isSelected())
                elif item.parentItem() and isinstance(item.parentItem(), ControlItem):
                    item.parentItem().setSelected(not item.parentItem().isSelected())
            else:
                # Обычный клик: если элемент еще не выделен, сбрасываем старое выделение и выбираем этот
                target = item if isinstance(item, ControlItem) else item.parentItem()
                if isinstance(target, ControlItem) and not target.isSelected():
                    self.clearSelection()
                    target.setSelected(True)

        # Пробрасываем клик вглубь фреймворка Qt Graphics View
        super().mousePressEvent(event)

        # Синхронизируем панели свойств под текущую группу выделения
        selected = self.selectedItems()
        if hasattr(self, 'select_control'):
            if len(selected) == 1:
                self.select_control(selected[0])
            elif len(selected) > 1:
                self.select_control(selected)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Обработка перемещения мыши по холсту."""
        super().mouseMoveEvent(event)

        # Транслируем координаты мыши относительно бланка формы в статус-бар
        if hasattr(self, 'background') and self.background:
            local_form_pos = self.background.mapFromScene(event.scenePos())
            if hasattr(self.background, 'status_bar') and self.background.status_bar:
                sb = self.background.status_bar
                if hasattr(sb, 'set_coordinates'):
                    sb.set_coordinates(local_form_pos.x(), local_form_pos.y())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Обработка отпускания кнопки мыши."""
        super().mouseReleaseEvent(event)

        # Если после резиновой рамки или драга изменился состав выделения
        selected = self.selectedItems()
        if hasattr(self, 'select_control'):
            if len(selected) == 1:
                self.select_control(selected[0])
            elif len(selected) > 1:
                self.select_control(selected)
