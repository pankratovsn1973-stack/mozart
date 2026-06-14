# mozart_import/graph/graphics_items.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsTextItem,
                             QGraphicsProxyWidget, QCheckBox, QGraphicsItem)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPen, QFont

from ..core.models import Field, NodeType

SOURCE_ID_FIELD = 'sourceid'


class FieldItem(QGraphicsRectItem):
    """Поле внутри прямоугольника таблицы/сущности. Может иметь чекбокс (для источника)."""
    def __init__(self, field: Field, show_checkbox: bool = False, is_sourceid: bool = False, parent=None):
        super().__init__(parent)
        self.field = field
        self.show_checkbox = show_checkbox
        self.is_sourceid = is_sourceid
        width = 200
        self.setRect(0, 0, width, 22)

        if is_sourceid:
            self.setBrush(QBrush(QColor(200, 200, 200)))
            self.setPen(QPen(Qt.darkGray))
        else:
            self.setBrush(QBrush(QColor(240, 240, 240)))
            self.setPen(QPen(Qt.black))

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        y_offset = 2
        if show_checkbox and not is_sourceid:
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(True)
            self.proxy = QGraphicsProxyWidget(self)
            self.proxy.setWidget(self.checkbox)
            self.proxy.setPos(5, y_offset)
            text_x = 25
        else:
            self.checkbox = None
            text_x = 5 if not is_sourceid else 25

        label = f"🔑 {field.name}" if is_sourceid else field.name
        self.text = QGraphicsTextItem(label, self)
        self.text.setDefaultTextColor(Qt.black)
        self.text.setPos(text_x, y_offset)

    def hoverEnterEvent(self, event):
        if not self.is_sourceid:
            self.setBrush(QBrush(QColor(200, 230, 255)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_sourceid:
            self.setBrush(QBrush(QColor(240, 240, 240)))
        super().hoverLeaveEvent(event)

    def is_checked(self) -> bool:
        if self.checkbox:
            return self.checkbox.isChecked()
        return False

    def set_checked(self, state: bool):
        if self.checkbox:
            self.checkbox.setChecked(state)

    def boundingRect(self):
        return self.rect()


class NodeItem(QGraphicsRectItem):
    """Прямоугольник таблицы/сущности с чекбоксом в заголовке (для выбора таблицы) и чекбоксами полей (для источника)."""
    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.field_items = []

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        width = 240
        field_count = len(node.fields)
        height = 30 + field_count * 22
        self.setRect(0, 0, width, height)

        if node.node_type == NodeType.SOURCE_TABLE:
            bg_color = QColor(220, 255, 220)  # светло-зелёный
        else:
            bg_color = QColor(255, 255, 200)  # светло-жёлтый
        self.setBrush(QBrush(bg_color))
        self.setPen(QPen(Qt.black, 2))

        # Чекбокс заголовка (выбор всей таблицы)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(False)
        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.checkbox)
        self.proxy.setPos(5, 5)

        self.title = QGraphicsTextItem(node.name, self)
        self.title.setDefaultTextColor(Qt.darkBlue)
        self.title.setFont(QFont("Arial", 10, QFont.Bold))
        self.title.setPos(25, 5)

        # Поля
        y = 30
        show_checkbox = (node.node_type == NodeType.SOURCE_TABLE)
        for field in node.fields:
            is_sid = (field.name == SOURCE_ID_FIELD) and (node.node_type == NodeType.MOZART_ENTITY)
            fi = FieldItem(field, show_checkbox=show_checkbox, is_sourceid=is_sid, parent=self)
            fi.setPos(10, y)
            self.field_items.append(fi)
            y += 22

        self.setPos(node.x, node.y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            new_pos = value
            new_pos.setY(max(0, new_pos.y()))
            if self.scene() and hasattr(self.scene(), 'divider_x'):
                divider_x = self.scene().divider_x
                if self.node.node_type == NodeType.SOURCE_TABLE:
                    max_x = divider_x - self.rect().width() - 10
                    new_pos.setX(max(10, min(new_pos.x(), max_x)))
                else:
                    min_x = divider_x + 10
                    new_pos.setX(max(min_x, new_pos.x()))
            return new_pos
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """После перемещения вручную обновляем линии."""
        super().mouseReleaseEvent(event)
        # Обновляем все линии сцены
        if self.scene() and hasattr(self.scene(), 'update_all_links'):
            self.scene().update_all_links()

    def update_position(self):
        self.node.x = self.pos().x()
        self.node.y = self.pos().y()

    def is_checked(self) -> bool:
        """Чекбокс заголовка."""
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool):
        self.checkbox.setChecked(checked)

    def get_checked_fields(self):
        """Возвращает имена полей, отмеченных чекбоксами (только для источника)."""
        if self.node.node_type != NodeType.SOURCE_TABLE:
            return [fi.field.name for fi in self.field_items]
        return [fi.field.name for fi in self.field_items if fi.is_checked()]

    def set_all_checked(self, checked: bool):
        """Отметить/снять все поля (источник)."""
        for fi in self.field_items:
            if not fi.is_sourceid:
                fi.set_checked(checked)