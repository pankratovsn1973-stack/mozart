# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item_context.py

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsItem


class ControlItemContext:
    """Миксин контекста: отвечает за отрисовку рамки выделения и управление маркерами изменения размеров."""

    def clear_internal_selection(self):
        """Сброс синих рамок выделения со всех внутренних подконтролов."""
        if hasattr(self, '_selected_child_widgets') and self._selected_child_widgets:
            for handle in self._selected_child_widgets:
                if hasattr(handle, 'setVisible'):
                    handle.setVisible(False)
            self._selected_child_widgets.clear()
        if hasattr(self, 'update'):
            self.update()

    def handle_internal_click(self, event):
        """Активация контекста внутренней части составного референса при каскадном клике."""
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
            child_name = getattr(child, 'name', child.objectName())
            if child_name in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref'):
                # Фиксируем активный дочерний контекст на сцене
                self.scene()._active_context_container = self
                self._active_child_item = child

                # Переключаем инспектор свойств на конкретную деталь референса
                if hasattr(self.scene(), 'select_control'):
                    self.scene().select_control(self)

                self.update_handles_position()
                self.update()

    def update_handles_position(self):
        """Синхронизация положения маркеров ресайза (хэндлов) вслед за изменением размеров родителя."""
        if not self.isSelected():
            return

        # Инициализируем массив маркеров, если он не был создан в конструкторе
        if not hasattr(self, '_selected_child_widgets') or self._selected_child_widgets is None:
            self._selected_child_widgets = []

        rect = self.rect()
        # Если маркеры еще не созданы на сцене — генерируем юго-восточную точку ресайза
        if not self._selected_child_widgets and self.scene():
            from .resize_handle import ResizeHandle  # Динамический импорт класса маркера

            # Строим маркер изменения размеров (Handles)
            handle = ResizeHandle(self)
            self.scene().addItem(handle)
            self._selected_child_widgets.append(handle)

        # Выравниваем маркер строго по юго-восточному углу (правый нижний край)
        for handle in self._selected_child_widgets:
            handle.setPos(rect.width(), rect.height())
            handle.setVisible(True)

    def paint(self, painter, option, widget):
        """Переопределение отрисовки прокси: нативное наложение FoxPro-style синей рамки выделения."""
        """Переопределение отрисовки прокси: нативное наложение FoxPro-style синей рамки выделения."""
        # ДОБАВЛЕН ТОЧЕЧНЫЙ ПРИНТ ДЛЯ ПРОВЕРКИ ВЫЗОВА ОТРИСОВКИ ГРАНИЦ
        print(f"[PAINT_BORDER] Метод paint вызвался! ID: {getattr(self, 'control_id', 'unknown')} | Выбран: {self.isSelected()}")



        # Вызываем базовую C++ отрисовку Qt-виджета (кнопок, текста, инпутов)
        super().paint(painter, option, widget)

        # Рисуем рамку фокуса только если элемент выбран пользователем
        if self.isSelected():
            painter.save()

            # Настройка пера: классический синий low-code пунктир толщиной 1.5 пикселя
            pen = QPen(QColor(0, 120, 215), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Рисуем контур строго по внешним границам геометрии прокси-контейнера
            rect = self.rect()
            painter.drawRect(rect)

            painter.restore()
