# widgets/form_designer_old/form_background.py
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtWidgets import QGraphicsObject, QGraphicsRectItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainter


class TitleBarStub(QGraphicsObject):
    """
    Заголовок формы.
    Использует локальные координаты мыши для перемещения.
    """

    form_moved = Signal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setZValue(1.0)
        self._is_dragging = False
        self._drag_start_pos = QPointF()

    def get_height(self) -> float:
        return 32.0

    def boundingRect(self):
        if self.parentItem():
            form = self.parentItem()
            parent_w = form._width if hasattr(form, '_width') else 400
            return QRectF(0.0, 0.0, parent_w, self.get_height())
        return QRectF(0.0, 0.0, 200.0, self.get_height())

    def paint(self, painter, option, widget):
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parentItem():
            self._is_dragging = True
            self._drag_start_pos = event.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging and self.parentItem():
            form = self.parentItem()

            delta = event.pos() - self._drag_start_pos
            parent_delta = form.mapToParent(delta) - form.mapToParent(QPointF(0, 0))
            new_pos = form.pos() + parent_delta

            if self.scene():
                scene_rect = self.scene().sceneRect()
                new_pos.setX(max(0.0, min(new_pos.x(), scene_rect.width() - form._width)))
                new_pos.setY(max(0.0, min(new_pos.y(), scene_rect.height() - form._height)))

            form.setPos(new_pos)

            if hasattr(form, 'update_handles_position'):
                form.update_handles_position()

            self.form_moved.emit(new_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class StatusBarStub(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPen(Qt.PenStyle.NoPen)
        self.setBrush(Qt.BrushStyle.NoBrush)

    def get_height(self) -> float:
        return 24.0


class FormBackground(QGraphicsObject):
    form_geometry_changed = Signal()
    form_resized = Signal(float, float)

    def __init__(self, width: float = 400, height: float = 300, title: str = "", parent=None):
        super().__init__(parent)
        self.title = str(title)
        self._show_grid = True
        self._grid_size = 10
        self.form_alias = ""
        self._handles = []

        self._width = float(width)
        self._height = float(height)

        self.setPos(0, 0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.setZValue(-100)

        self.title_bar = TitleBarStub(self)
        self.status_bar = StatusBarStub(self)
        self.title_bar.form_moved.connect(self._on_form_moved)

    def _on_form_moved(self, new_pos):
        if self.scene() and hasattr(self.scene(), 'form_moved'):
            self.scene().form_moved.emit()

    def rect(self):
        return QRectF(0, 0, self._width, self._height)

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    @property
    def x(self) -> float:
        return self.pos().x()

    @property
    def y(self) -> float:
        return self.pos().y()

    def boundingRect(self):
        return QRectF(0, 0, self._width, self._height)

    def set_show_grid(self, show: bool):
        if self._show_grid != show:
            self._show_grid = show
            self.update()

    def set_grid_size(self, size: int):
        new_size = max(2, int(size))
        if self._grid_size != new_size:
            self._grid_size = new_size
            self.update()

    def update_handles_position(self):
        for handle in self._handles:
            if handle and hasattr(handle, 'update_position'):
                handle.update_position()

    def update_geometry(self, parent_x: float, parent_y: float, width: float, height: float):
        w = max(50.0, float(width))
        h = max(50.0, float(height))

        self.prepareGeometryChange()

        if hasattr(self, 'title_bar') and self.title_bar:
            self.title_bar.prepareGeometryChange()

        self._width = w
        self._height = h
        self.setPos(QPointF(parent_x, parent_y))

        self.update()
        self.update_handles_position()

        if self.scene():
            self.form_resized.emit(w, h)
            self.form_geometry_changed.emit()
            self.scene().update()

    def resize_form(self, width: float, height: float):
        pos = self.pos()
        self.update_geometry(pos.x(), pos.y(), width, height)

    def set_width(self, width: float):
        pos = self.pos()
        self.update_geometry(pos.x(), pos.y(), width, self._height)

    def set_height(self, height: float):
        pos = self.pos()
        self.update_geometry(pos.x(), pos.y(), self._width, height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        rect = self.rect()

        painter.fillRect(rect, QColor('#ffffff'))

        if self._show_grid and self._grid_size > 0:
            grid_pen = QPen(QColor('#d0d0d0'), 0, Qt.PenStyle.SolidLine)
            painter.setPen(grid_pen)
            left = int(rect.left())
            right = int(rect.right())
            top = int(rect.top())
            bottom = int(rect.bottom())
            step = int(self._grid_size)

            x = left + step
            while x < right:
                painter.drawLine(x, top, x, bottom)
                x += step

            y = top + step
            while y < bottom:
                painter.drawLine(left, y, right, y)
                y += step

        painter.setPen(QPen(QColor('#808080'), 1, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        painter.fillRect(rect.x(), rect.y(), rect.width(), 32, QColor('#d8d8d8'))
        painter.setPen(QPen(QColor('#000000')))
        painter.drawText(rect.x() + 8, rect.y(), rect.width() - 16, 32,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.title)

        sb_y = rect.bottom() - 24
        painter.fillRect(rect.x(), sb_y, rect.width(), 24, QColor('#e0e0e0'))
        painter.setPen(QPen(QColor('#b0b0b0'), 1))
        painter.drawLine(rect.x(), sb_y, rect.right(), sb_y)
        painter.setPen(QPen(QColor('#555555')))
        painter.drawText(rect.x() + 8, sb_y, rect.width() - 16, 24,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Готово")

        painter.restore()
