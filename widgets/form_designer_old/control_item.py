# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item.py

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QWidget
from .control_item_movement import ControlItemMovement
from .focus_registry import FocusRegistry


class ControlItem(ControlItemMovement):
    """Главный управляющий класс графического прокси-контейнера на сцене визуального дизайнера."""
    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        self.control_id = str(control_id).strip()
        self._selected_child_widgets = []
        self._active_child_item = None
        super().__init__(widget, control_id, control_type, parent)

    def clear_internal_selection(self):
        """Сброс и скрытие маркеров изменения размеров."""
        if hasattr(self, '_selected_child_widgets') and self._selected_child_widgets:
            for handle in self._selected_child_widgets:
                if hasattr(handle, 'setVisible'):
                    handle.setVisible(False)
            self._selected_child_widgets.clear()
        self.update()

    def handle_internal_click(self, event):
        """Активация контекста внутренней части составного референса при каскадном клике."""
        if not self.scene():
            return

        source_widget = self.widget()
        if not source_widget:
            return

        child = source_widget.childAt(event.pos().toPoint())
        if not child and event.widget():
            child = event.widget()

        if child and child != source_widget:
            child_name = getattr(child, 'name', child.objectName())
            if child_name in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref'):
                self.scene()._active_context_container = self
                self._active_child_item = child

                if hasattr(self.scene(), 'select_control'):
                    self.scene().select_control(self)

                self.update_handles_position()
                self.update()

    def update_handles_position(self):
        """Синхронизация положения маркера юго-восточного ресайза за правым нижним углом рамки."""
        # ДОБАВЛЕН ПРИНТ ДЛЯ ПРОВЕРКИ СТАРТА ОПРЕДЕЛЕНИЯ МАРКЕРОВ
        print(
            f"[HANDLE_LOG] Шаг 1: Запуск update_handles_position() для ID: {self.control_id} | Выбран: {self.isSelected()}")

        if not self.isSelected():
            return

        if not hasattr(self, '_selected_child_widgets') or self._selected_child_widgets is None:
            self._selected_child_widgets = []

        rect = self.rect()

        # Если маркер еще не создан на сцене — генерируем его напрямую в основном классе
        if not self._selected_child_widgets and self.scene():
            try:
                from .resize_handle import ResizeHandle
                print(f"[HANDLE_LOG] Шаг 2: Попытка инстанцировать ResizeHandle для родителя {self.control_id}")
                handle = ResizeHandle(self)
                self.scene().addItem(handle)
                self._selected_child_widgets.append(handle)
                print("[HANDLE_LOG] Шаг 3: Маркер ResizeHandle успешно добавлен на сцену")
            except Exception as e:
                print(f"[HANDLE_LOG] КРИТИЧЕСКАЯ ОШИБКА создания ResizeHandle: {e}")

        # Выравниваем маркер строго по юго-восточному углу (правый нижний край)
        for handle in self._selected_child_widgets:
            try:
                handle.setPos(rect.width(), rect.height())
                handle.setVisible(True)
                if hasattr(handle, 'update'):
                    handle.update()
                print(f"[HANDLE_LOG] Шаг 4: Позиция маркера выставлена на {rect.width()}x{rect.height()}")
            except Exception as e:
                print(f"[HANDLE_LOG] ОШИБКА позиционирования хэндла: {e}")

    def paint(self, painter, option, widget):
        """Переопределение отрисовки: жесткое наложение FoxPro-style синей рамки выделения."""
        super().paint(painter, option, widget)

        if self.isSelected():
            from PySide6.QtGui import QPen, QColor
            painter.save()
            pen = QPen(QColor(0, 120, 215), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect = self.rect()
            painter.drawRect(rect)
            painter.restore()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Перехват клика мыши: разделение верхнего уровня, каскадного фокуса и свободного драга."""
        if event.button() == Qt.MouseButton.RightButton:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:

            # УРОВЕНЬ 1: Составной контрол еще не выбран — берем его монолитно и готовим к движению
            if not self.isSelected():
                self._is_dragging = True
                self._drag_start_pos = event.scenePos()

                if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    if self.scene():
                        self.scene().clearSelection()
                        FocusRegistry().reset_active_context()

                self.setSelected(True)

                self.clear_internal_selection()
                self.selected_changed.emit(True)

                if self.scene() and hasattr(self.scene(), 'select_control'):
                    self.scene().select_control(self)

                self.update_handles_position()
                self.update()

                event.accept()
                return

            # УРОВЕНЬ 2: Контрол УЖЕ выбран — проверяем каскадный фокус на под-элементы
            source_widget = self.widget()
            if source_widget:
                child = source_widget.childAt(event.pos().toPoint())
                if not child and event.widget():
                    child = event.widget()

                if child and child != source_widget:
                    child_name = getattr(child, 'name', child.objectName())
                    if child_name in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref'):
                        if self.scene() and getattr(self.scene(), '_active_context_container', None) == self:
                            self.handle_internal_click(event)
                            super().mousePressEvent(event)
                            return

            # УРОВЕНЬ 3: Клик по пустому месту — сброс внутренностей на внешнюю рамку
            self.clear_internal_selection()
            FocusRegistry().reset_active_context()

            self._is_dragging = True
            self._drag_start_pos = event.scenePos()

            self.update_handles_position()
            self.update()

            event.accept()
            return

        super().mousePressEvent(event)
