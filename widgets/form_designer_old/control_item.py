# widgets/form_designer_old/control_item.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс ControlItem (наследник QGraphicsProxyWidget).
Является визуальным контейнером-оберткой для элементов управления в дизайнере.
Исправлен баг блокировки простых контролов (TextBox, ComboBox) через прозрачный Event Filter.
"""

from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsSceneMouseEvent, QWidget, QApplication
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QEvent


class ControlItem(QGraphicsProxyWidget):
    """
    Прокси-виджет для управления контролами на холсте дизайнере.
    Обеспечивает плавное перемещение любых типов полей без блокировки выделения в Qt.
    """
    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        super().__init__(parent)
        self.setWidget(widget)

        self.control_id = str(control_id)
        self.control_type = control_type

        # Настраиваем нативные флаги интерактивности графического движка Qt
        self.setFlag(QGraphicsProxyWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.geometryChanged.connect(self._forward_geometry_signal)

        self._is_dragging = False
        self._drag_start_pos = QPointF()

        # Накатываем фильтр событий на внутренний виджет и всех его детей каскадно
        if widget:
            widget.installEventFilter(self)
            for child in widget.findChildren(QWidget):
                child.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        """
        Перехватчик низкоуровневых событий рантайм-виджетов.
        ИСПРАВЛЕНО: Фильтр больше НИКОГДА не возвращает True для кликов,
        полностью исключая мёртвое залипание текстбоксов.
        """
        if QApplication.activeModalWidget() is not None:
            return False

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # Оповещаем сцену о том, какой внутренний виджет кликнули
            if self.scene() and hasattr(self.scene(), 'select_control'):
                self.scene().select_control(self.widget())

            # Инициируем параметры для плавного нативного таскания мышью
            self._is_dragging = True

            # Рассчитываем стартовую позицию захвата в координатах сцены
            scene_pos = self.mapToScene(QPointF(event.position().x(), event.position().y()))
            self._drag_start_pos = scene_pos - self.pos()

            # Принудительно выделяем прокси на сцене
            self.setSelected(True)

            # КРИТИЧЕСКИЙ ФИКС: Возвращаем False! Позволяем Qt обработать клик штатно,
            # благодаря чему TextBox и ComboBox начнут легально выделяться и двигаться.
            return False

        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self._is_dragging = False

            # Примагничиваем к сетке при отпускании
            if self.scene() and hasattr(self.scene(), 'snap_to_grid'):
                snapped_pos = self.scene().snap_to_grid(self.pos())
                self.setPos(snapped_pos)
            return False

        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Нативная обработка нажатия мыши на холсте сцены."""
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.scenePos() - self.pos()
            if self.scene() and hasattr(self.scene(), 'select_control'):
                self.scene().select_control(self.widget())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Нативное плавное перемещение элементов по осям X и Y."""
        if not self._is_dragging:
            super().mouseMoveEvent(event)
            return

        # Рассчитываем чистую позицию без рывков и округлений
        new_pos = event.scenePos() - self._drag_start_pos

        # Удерживаем контрол строго в рамках границ подложки формы
        if self.parentItem():
            p_rect = self.parentItem().rect()
            my_rect = self.rect()

            min_y = 32.0  # Защита шапки TitleBar
            max_y = max(min_y, p_rect.height() - my_rect.height() - 24.0)  # Защита StatusBar
            max_x = max(0.0, p_rect.width() - my_rect.width())

            x = max(0.0, min(new_pos.x(), max_x))
            y = max(min_y, min(new_pos.y(), max_y))
            new_pos = QPointF(x, y)

        self.setPos(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Мягкий магнить к сетке при отпускании мыши на сцене."""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            if self.scene() and hasattr(self.scene(), 'snap_to_grid'):
                snapped_pos = self.scene().snap_to_grid(self.pos())
                self.setPos(snapped_pos)
        super().mouseReleaseEvent(event)

    def _forward_geometry_signal(self):
        """Отправка координат в инспектор свойств."""
        rect = self.rect()
        pos = self.pos()
        self.geometry_changed.emit(self.control_id, int(pos.x()), int(pos.y()), int(rect.width()), int(rect.height()))

    def set_selected(self, selected: bool):
        self.setSelected(selected)
        inner_widget = self.widget()
        if inner_widget and hasattr(inner_widget, 'set_selected'):
            inner_widget.set_selected(selected)
        if not selected and self.scene():
            self.clearFocus()

    def itemChange(self, change, value):
        if change == QGraphicsProxyWidget.ItemSelectedChange and self.scene():
            is_selected = bool(value)
            self.selected_changed.emit(is_selected)
            inner_widget = self.widget()
            if inner_widget and hasattr(inner_widget, 'set_selected'):
                inner_widget.set_selected(is_selected)
        return super().itemChange(change, value)
