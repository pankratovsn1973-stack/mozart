# mozart_import/graph/link_line.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QPen, QColor

from ..core.models import LinkType


class LinkLine(QGraphicsLineItem):
    """
    Линия связи между двумя полями.
    Хранит полный набор маппингов для данной связи импорта.
    Теперь поддерживает выделение и удаление.
    """
    COLORS = {
        LinkType.IMPORT: QColor(200, 30, 30),      # красный
        LinkType.FK_SOURCE: QColor(100, 100, 140),  # сине-серый
        LinkType.COMPOSITION: QColor(30, 150, 30),  # зелёный
    }

    def __init__(self, start_item, start_field_item, end_item, end_field_item,
                 link_type: LinkType, mappings=None):
        super().__init__()
        self.start_item = start_item
        self.start_field_item = start_field_item
        self.end_item = end_item
        self.end_field_item = end_field_item
        self.link_type = link_type
        # Маппинги: список словарей {source_field, target_field, is_source_id}
        self.mappings = mappings or []
        # Если маппинги не заданы, создаём один на основе начального поля
        if not self.mappings and link_type == LinkType.IMPORT:
            self.mappings = [{
                'source_field': start_field_item.field.name,
                'target_field': end_field_item.field.name,
                'is_source_id': False
            }]

        color = self.COLORS.get(link_type, Qt.black)
        width = 3 if link_type == LinkType.IMPORT else 1
        style = Qt.SolidLine if link_type == LinkType.IMPORT else Qt.DashLine

        # Пера для обычного и выделенного состояния
        self._normal_pen = QPen(color, width, style)
        self._selected_pen = QPen(Qt.red, width + 1, style)

        self.setPen(self._normal_pen)
        self.setZValue(-1)
        # Разрешаем выделение линии
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsLineItem.ItemSendsGeometryChanges, True)
        self.update_position()

    def itemChange(self, change, value):
        """При выделении меняем цвет линии."""
        if change == QGraphicsLineItem.ItemSelectedChange:
            if value:
                self.setPen(self._selected_pen)
            else:
                self.setPen(self._normal_pen)
        return super().itemChange(change, value)

    def update_position(self):
        if not self.start_field_item or not self.end_field_item:
            return
        sp = self.start_field_item.scenePos()
        sp.setX(sp.x() + self.start_field_item.boundingRect().width())
        sp.setY(sp.y() + self.start_field_item.boundingRect().height() / 2)

        ep = self.end_field_item.scenePos()
        ep.setX(ep.x())
        ep.setY(ep.y() + self.end_field_item.boundingRect().height() / 2)

        self.setLine(QLineF(sp, ep))

    def update_mappings_from_dialog(self, new_mappings):
        """Обновить маппинги после диалога."""
        self.mappings = new_mappings