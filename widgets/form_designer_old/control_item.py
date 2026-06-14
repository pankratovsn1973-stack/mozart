# widgets/form_designer_old/control_item.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс ControlItem (наследник QGraphicsProxyWidget).
Является визуальным контейнером-оберткой для элементов управления в дизайнере.
Исправлен баг аппаратной блокировки мыши в модальных диалогах СУБД (QFileDialog / .mzt).
"""

from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsSceneMouseEvent, QWidget, QApplication
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QEvent


class ControlItem(QGraphicsProxyWidget):
    """
    Прокси-виджет для управления контролами на холсте дизайнера.
    Перехватывает события мыши активных виджетов, автоматически уступая фокус модальным окнам.
    """
    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        super().__init__(parent)
        self.setWidget(widget)

        self.control_id = str(control_id)
        self.control_type = control_type

        # Включаем интерактивные флаги сцены
        self.setFlag(QGraphicsProxyWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.geometryChanged.connect(self._forward_geometry_signal)

        self._is_dragging = False
        self._drag_start_pos = QPointF()

        # МАГИЯ ФОКСПРО: Накатываем фильтр событий на внутренний виджет и всех его детей
        if widget:
            widget.installEventFilter(self)
            for child in widget.findChildren(QWidget):
                child.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        """
        Перехватчик низкоуровневых событий Qt.
        Освобождает мышь, если в приложении открыт любой модальный диалог выбора файлов.
        """
        # ЖЕЛЕЗНАЯ ЗАЩИТА: Проверяем, нет ли в системе активного модального окна (диалога .mzt)
        # Если диалог открыт, мы полностью отключаем фильтрацию и отдаем мышь окну
        if QApplication.activeModalWidget() is not None:
            self._is_dragging = False
            return False  # Пропускаем событие дальше, мышь в диалоге РАБОТАЕТ

        if not self.isSelected():
            return super().eventFilter(obj, event)

        if event.type() in [QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease]:
            local_pos = self.mapFromGlobal(event.globalPosition().toPoint())

            # Проверяем, что кликают именно внутри геометрии нашего контрола на холсте
            if not self.rect().contains(QPointF(local_pos.x(), local_pos.y())):
                return False

            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._is_dragging = True
                self._drag_start_pos = QPointF(local_pos.x(), local_pos.y())

                if self.scene() and hasattr(self.scene(), 'select_control'):
                    self.scene().select_control(self.widget())
                self.setSelected(True)
                return True  # Поглощаем событие, блокируя рантайм-ввод поля

            elif event.type() == QEvent.MouseMove and self._is_dragging:
                if self.scene():
                    scene_pos = self.scene().views().mapToScene(
                        self.scene().views().mapFromGlobal(event.globalPosition().toPoint())
                    )
                    new_pos = scene_pos - self._drag_start_pos

                    if hasattr(self.scene(), 'snap_to_grid'):
                        new_pos = self.scene().snap_to_grid(new_pos)

                    self._restrict_and_set_pos(new_pos)
                return True

            elif event.type() == QEvent.MouseButtonRelease:
                self._is_dragging = False
                return True

        return super().eventFilter(obj, event)

    def _restrict_and_set_pos(self, new_pos: QPointF):
        """Удерживает элемент строго в рамках границ родительской формы."""
        if self.parentItem():
            p_rect = self.parentItem().rect()
            my_rect = self.rect()

            max_x = max(0.0, p_rect.width() - my_rect.width())
            max_y = max(0.0, p_rect.height() - my_rect.height())

            x = max(0.0, min(new_pos.x(), max_x))
            y = max(0.0, min(new_pos.y(), max_y))
            new_pos = QPointF(x, y)

        self.setPos(new_pos)

    def _forward_geometry_signal(self):
        rect = self.rect()
        pos = self.pos()
        self.geometry_changed.emit(self.control_id, int(pos.x()), int(pos.y()), int(rect.width()), int(rect.height()))

    def set_selected(self, selected: bool):
        self.setSelected(selected)
        inner_widget = self.widget()
        if inner_widget and hasattr(inner_widget, 'set_selected'):
            inner_widget.set_selected(selected)

        # Если элемент снимается с выделения, принудительно сбрасываем фокус сцены
        if not selected and self.scene():
            self.clearFocus()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.scenePos() - self.pos()
            if self.scene() and hasattr(self.scene(), 'select_control'):
                self.scene().select_control(self.widget())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self._is_dragging:
            super().mouseMoveEvent(event)
            return
        new_pos = event.scenePos() - self._drag_start_pos
        if self.scene() and hasattr(self.scene(), 'snap_to_grid'):
            new_pos = self.scene().snap_to_grid(new_pos)
        self._restrict_and_set_pos(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsProxyWidget.ItemSelectedChange and self.scene():
            is_selected = bool(value)
            self.selected_changed.emit(is_selected)
            inner_widget = self.widget()
            if inner_widget and hasattr(inner_widget, 'set_selected'):
                inner_widget.set_selected(is_selected)
            if not is_selected:
                self.clearFocus()
        return super().itemChange(change, value)
