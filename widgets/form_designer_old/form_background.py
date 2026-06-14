# widgets/form_designer_old/form_background.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс FormBackground (наследник QGraphicsRectItem).
Является визуальной подложкой (холстом проектируемой формы) на сцене дизайнера.
Исправлен баг отрыва волшебных точек формы путем циклического перевыделения состояния.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter


class TitleBarStub(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPen(Qt.NoPen)
        self.setBrush(Qt.NoBrush)
        self.setAcceptHoverEvents(False)

    def get_height(self) -> float: return 32.0


class ToolBarStub(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPen(Qt.NoPen)
        self.setBrush(Qt.NoBrush)
        self.setAcceptHoverEvents(False)

    def get_height(self) -> float: return 0.0


class StatusBarStub(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPen(Qt.NoPen)
        self.setBrush(Qt.NoBrush)
        self.setAcceptHoverEvents(False)

    def get_height(self) -> float: return 24.0


class FormBackground(QGraphicsRectItem):
    """Класс подложки формы для визуального редактора."""

    def __init__(self, width: float = 400, height: float = 300, title: str = "", parent=None):
        super().__init__(parent)
        self.title = str(title)

        self.title_bar = TitleBarStub()
        self.tool_bar = ToolBarStub()
        self.status_bar = StatusBarStub()

        w = float(width) if not isinstance(width, str) else 400.0
        h = float(height) if not isinstance(height, str) else 300.0
        self.setRect(0.0, 0.0, w, h)
        self.setPos(0.0, 0.0)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

        self.setPen(QPen(QColor('#808080'), 1, Qt.SolidLine))
        self.setBrush(QColor('#ffffff'))

    @property
    def width(self) -> float:
        return self.rect().width()

    @property
    def height(self) -> float:
        return self.rect().height()

    def boundingRect(self) -> QRectF:
        """Явный пересчет физических границ холста формы для фреймворка Qt."""
        return self.rect().adjusted(-1, -1, 1, 1)

    def resize_form(self, width: float, height: float):
        """
        Метод безопасного изменения размеров формы из инспектора свойств.
        ИСПРАВЛЕНО: Временный сброс выделения принудительно прижимает точки к краям.
        """
        w = max(50.0, float(width))
        h = max(50.0, float(height))

        self.prepareGeometryChange()
        self.setRect(0.0, 0.0, w, h)

        if self.scene():
            self.scene().setSceneRect(self.scene().itemsBoundingRect())

            # ФОКС-ТРЮК: Если форма выделена, временно снимаем выделение и возвращаем его.
            # Это аппаратно заставляет Qt уничтожить старую рамку пунктира и нарисовать точки точно по новым краям!
            if self.isSelected():
                self.setSelected(False)
                self.setSelected(True)

            # Перерисовываем вьюпорт
            for view in self.scene().views():
                if view.viewport():
                    view.viewport().update()

            if hasattr(self.scene(), '_refresh_grid_layers'):
                self.scene()._refresh_grid_layers()
            else:
                self.scene().update()

    def set_width(self, width: float):
        self.resize_form(width, self.rect().height())

    def set_height(self, height: float):
        self.resize_form(self.rect().width(), height)

    def paint(self, painter: QPainter, option, widget=None):
        """Визуальная отрисовка элементов окна формы прямо на её теле."""
        painter.save()

        # 1. Рамка формы
        border_pen = QPen(QColor('#808080'), 1, Qt.SolidLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect())

        # 2. Заголовок (TitleBar)
        if self.title_bar:
            tb_height = self.title_bar.get_height()
            tb_rect = QRectF(self.rect().left(), self.rect().top(), self.rect().width(), tb_height)
            painter.fillRect(tb_rect, QColor('#d8d8d8'))
            painter.drawRect(tb_rect)

            painter.setPen(QPen(QColor('#000000')))
            painter.drawText(tb_rect.adjusted(8, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, self.title)

        # 3. Статус-бар (StatusBar)
        if self.status_bar:
            sb_height = self.status_bar.get_height()
            sb_rect = QRectF(self.rect().left(), self.rect().bottom() - sb_height, self.rect().width(), sb_height)
            painter.fillRect(sb_rect, QColor('#e0e0e0'))
            painter.setPen(QPen(QColor('#b0b0b0'), 1))
            painter.drawLine(sb_rect.left(), sb_rect.top(), sb_rect.right(), sb_rect.top())

            painter.setPen(QPen(QColor('#555555')))
            painter.drawText(sb_rect.adjusted(8, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Ready")

        painter.restore()
