# widgets/form_designer_old/control_item.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsItem, QWidget, QApplication
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QEvent
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from .resize_handle import ResizeHandle


class ControlItem(QGraphicsProxyWidget):
    """Прокси-виджет для управления контролами на холсте визуального дизайнера."""

    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        super().__init__(parent)
        self.setWidget(widget)

        self.control_id = str(control_id)
        self.control_type = control_type

        # Включаем стандартные флаги выделения и трекинга геометрии
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        # Полностью блокируем проваливание событий мыши во внутренние виджеты в режиме дизайна
        self.setFiltersChildEvents(True)

        # Переменные для ручного расчета перемещения
        self._is_dragging = False
        self._drag_start_pos = QPointF()

        # Автоматически инициализируем маркер ресайза, дочерний для этого контрола
        self.resize_handle = ResizeHandle(4, self, parent=self)
        self._handles = [self.resize_handle]
        self.resize_handle.setVisible(False)
        self.update_handles_position()

    def setWidgetSize(self, width, height):
        widget = self.widget()
        if widget:
            try:
                widget.setFixedSize(int(width), int(height))
                self.updateGeometry()
                self.update_handles_position()
                self._forward_geometry_signal()
            except Exception as e:
                print(f"[ControlItem] Ошибка ресайза виджета: {e}")

    def update_handles_position(self):
        if hasattr(self, '_handles'):
            for handle in self._handles:
                if handle and hasattr(handle, 'update_position'):
                    handle.update_position()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Обработка захвата контрола мышью."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True

            # Запоминаем стартовую позицию клика относительно левого верхнего угла самого контрола
            self._drag_start_pos = event.pos()

            # Управляем групповым или одиночным выделением
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.setSelected(not self.isSelected())
            else:
                if not self.isSelected():
                    if self.scene():
                        self.scene().clearSelection()
                    self.setSelected(True)

            # Фокусируем инспектор свойств
            if self.scene() and hasattr(self.scene(), 'select_control'):
                self.scene().select_control(self)

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Плавное перемещение текущего контрола (или всей группы выделенных элементов) мышью."""
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:

            # Если выделено несколько элементов, перемещаем их синхронно через сцену
            if self.scene():
                selected_items = [item for item in self.scene().selectedItems() if isinstance(item, ControlItem)]

                # Если выделена группа, рассчитываем общую дельту смещения по первому элементу
                if len(selected_items) > 1:
                    new_pos_scene = event.scenePos() - self._drag_start_pos
                    delta = new_pos_scene - self.pos()

                    for item in selected_items:
                        item._move_with_constraints(item.pos() + delta)
                    event.accept()
                    return

            # Одиночное перемещение
            new_pos = event.scenePos() - self._drag_start_pos
            self._move_with_constraints(new_pos)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Отпускание мыши и привязка к сетке."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

            # Применяем привязку к сетке по окончании движения
            if self.scene() and hasattr(self.scene(), 'snap_to_grid'):
                snapped_pos = self.scene().snap_to_grid(self.pos())
                self._move_with_constraints(snapped_pos)

            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _move_with_constraints(self, target_pos: QPointF):
        """Вспомогательный метод перемещения с жестким удержанием внутри границ бланка."""
        if self.parentItem() and hasattr(self.parentItem(), 'rect'):
            p_rect = self.parentItem().rect()
            my_rect = self.rect()

            min_y = 32.0  # Высота заголовка формы бланка
            max_y = max(min_y, p_rect.height() - my_rect.height() - 24.0)
            max_x = max(0.0, p_rect.width() - my_rect.width())

            x = max(0.0, min(target_pos.x(), max_x))
            y = max(min_y, min(target_pos.y(), max_y))
            target_pos = QPointF(x, y)

        self.setPos(target_pos)
        self.update_handles_position()
        self._forward_geometry_signal()

    def _forward_geometry_signal(self):
        rect = self.rect()
        pos = self.pos()
        self.geometry_changed.emit(
            self.control_id, int(pos.x()), int(pos.y()), int(rect.width()), int(rect.height())
        )
        if self.scene() and hasattr(self.scene(), 'geometry_changed'):
            self.scene().geometry_changed.emit(
                self.control_id, int(pos.x()), int(pos.y()), int(rect.width()), int(rect.height())
            )

        # МОНОЛИТНАЯ ПРОШИВКА СИНХРОНИЗАЦИИ: Напрямую находим панель свойств через иерархию окон приложения
        for widget in QApplication.allWidgets():
            if widget.__class__.__name__ == "FormDesigner":
                if hasattr(widget, 'property_panel') and hasattr(widget.property_panel, 'update_geometry_values'):
                    widget.property_panel.update_geometry_values(pos.x(), pos.y(), rect.width(), rect.height())
                    break

    def set_selected(self, selected: bool):
        self.setSelected(selected)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            is_selected = bool(value)
            self.selected_changed.emit(is_selected)

            if hasattr(self, '_handles'):
                for handle in self._handles:
                    handle.setVisible(is_selected)
                    if is_selected:
                        handle.update_position()

        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.update_handles_position()
            self._forward_geometry_signal()

        return super().itemChange(change, value)
