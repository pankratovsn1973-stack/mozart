# widgets/form_designer_old/form_background.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QApplication, QGraphicsScene
from PySide6.QtCore import Qt, Signal, QObject, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QFont, QPainter


class FormBackgroundSignals(QObject):
    form_resized = Signal(float, float)
    form_geometry_changed = Signal()


class FormBackground(QGraphicsRectItem):
    """Графический бланк формы с прорисованными секциями шапки, тулбара, подвала и внутренней сетки."""

    def __init__(self, width=800.0, height=600.0, title="Новая форма", parent=None):
        super().__init__(parent)
        self.signals = FormBackgroundSignals()

        self.form_resized = self.signals.form_resized
        self.form_geometry_changed = self.signals.form_geometry_changed

        self.form_alias = "new_form"
        self.title = str(title)
        self.form_role = "edit"
        self.entity_alias = ""
        self.interface_role_id = ""
        self.target_menu_id = ""

        self._width = float(width)
        self._height = float(height)

        self.setRect(0.0, 0.0, self._width, self._height)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setZValue(-10)

        self.setPen(QPen(QColor('#bcbcbc'), 1.5, Qt.PenStyle.SolidLine))
        self.setBrush(QBrush(QColor('#ffffff')))

        self._handles = []
        self._is_moving_form = False
        self._move_start_pos = QPointF()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def set_width(self, val):
        self.update_geometry(self.pos().x(), self.pos().y(), float(val), self._height)

    def set_height(self, val):
        self.update_geometry(self.pos().x(), self.pos().y(), self._width, float(val))

    def update_geometry(self, x, y, w, h):
        self.prepareGeometryChange()
        self._width = max(200.0, float(w))
        self._height = max(150.0, float(h))
        self.setRect(0.0, 0.0, self._width, self._height)

        from .designer_data_model import DesignerDataModel
        model = DesignerDataModel()
        model.set_value("form_root", "width", str(int(self._width)))
        model.set_value("form_root", "height", str(int(self._height)))

        for widget in QApplication.allWidgets():
            if widget.__class__.__name__ == "PropertyEditor":
                if getattr(widget, 'current_control_id', None) == "form_root":
                    widget.update_geometry_values(x, y, self._width, self._height)
                break

        if self.scene():
            self.scene().invalidate(self.scene().sceneRect(), QGraphicsScene.SceneLayer.BackgroundLayer)

        self.form_resized.emit(self._width, self._height)
        self.form_geometry_changed.emit()
        self.update_handles_position()

    def update_handles_position(self):
        if not self._handles: return
        handle = self._handles.__getitem__(0)
        offset = 2.0
        handle.setPos(self._width - offset, self._height - offset)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= 32.0:
            self._is_moving_form = True
            self._move_start_pos = event.scenePos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_moving_form:
            current_pos = event.scenePos()
            delta = current_pos - self._move_start_pos
            self._move_start_pos = current_pos

            new_pos = self.pos() + delta
            self.setPos(new_pos)

            from .designer_data_model import DesignerDataModel
            model = DesignerDataModel()
            model.set_value("form_root", "x", str(int(new_pos.x())))
            model.set_value("form_root", "y", str(int(new_pos.y())))

            for widget in QApplication.allWidgets():
                if widget.__class__.__name__ == "PropertyEditor":
                    if getattr(widget, 'current_control_id', None) == "form_root":
                        widget.update_geometry_values(new_pos.x(), new_pos.y(), self._width, self._height)
                    break

            self.form_geometry_changed.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_moving_form = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        painter.save()
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            header_h = 32.0
            toolbar_h = 28.0
            footer_h = 24.0
            work_top = header_h + toolbar_h
            work_bottom = self._height - footer_h

            grid_size = 10
            grid_visible = True
            if self.scene():
                grid_size = getattr(self.scene(), 'grid_size', 10)
                grid_visible = getattr(self.scene(), 'grid_visible', True)

            if grid_visible and grid_size > 0:
                grid_pen = QPen(QColor('#e8e8e8'), 0.5, Qt.PenStyle.SolidLine)
                painter.setPen(grid_pen)

                x_step = float(grid_size)
                while x_step < self._width:
                    painter.drawLine(x_step, work_top, x_step, work_bottom)
                    x_step += float(grid_size)

                y_step = work_top + (float(grid_size) - (work_top % float(grid_size)))
                while y_step < work_bottom:
                    painter.drawLine(0.0, y_step, self._width, y_step)
                    y_step += float(grid_size)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#e0e0e0')))
            painter.drawRect(QRectF(0, 0, self._width, header_h))

            painter.setPen(QPen(QColor('#333333')))
            font = QFont("Segoe UI", 10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(10, 0, self._width - 20, header_h),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#f0f0f0')))
            painter.drawRect(QRectF(0, header_h, self._width, toolbar_h))

            painter.setPen(QPen(QColor('#d0d0d0'), 1.0))
            painter.drawLine(0, work_top, self._width, work_top)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#f0f0f0')))
            painter.drawRect(QRectF(0, work_bottom, self._width, footer_h))

            painter.setPen(QPen(QColor('#d0d0d0'), 1.0))
            painter.drawLine(0, work_bottom, self._width, work_bottom)

            painter.setPen(QPen(QColor('#666666')))
            font_footer = QFont("Segoe UI", 9)
            painter.setFont(font_footer)
            painter.drawText(QRectF(10, work_bottom, self._width - 20, footer_h),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Готово")

            painter.setPen(QPen(QColor('#bcbcbc'), 1.5, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect())
        finally:
            painter.restore()
