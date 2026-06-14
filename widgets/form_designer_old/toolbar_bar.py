# /home/sergey/Documents/configurate/widgets/form_designer_old/toolbar_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout, QGraphicsProxyWidget, QComboBox
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont


class ToolBarButton(QGraphicsWidget):
    """Интерактивная кнопка на тулбаре с поддержкой фиксации (Checkable)"""

    clicked = Signal(str)
    toggled = Signal(bool)

    def __init__(self, symbol, tooltip="", parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.tooltip = tooltip
        self.is_hovered = False

        self._is_checkable = False
        self._is_checked = False

        self.setPreferredSize(28, 24)
        self.setAcceptHoverEvents(True)

    def setCheckable(self, checkable: bool):
        self._is_checkable = checkable
        self.update()

    def isCheckable(self) -> bool:
        return self._is_checkable

    def setChecked(self, checked: bool):
        if self._is_checked != checked:
            self._is_checked = checked
            self.toggled.emit(checked)
            self.update()

    def isChecked(self) -> bool:
        return self._is_checked

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        event.accept()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            if self._is_checkable:
                self.setChecked(not self._is_checked)
            self.clicked.emit(self.symbol)
            event.accept()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        if self._is_checked:
            painter.setBrush(QBrush(QColor(180, 210, 240)))
            painter.setPen(QPen(QColor(120, 160, 220), 1))
            painter.drawRoundedRect(self.rect(), 3, 3)
        elif self.is_hovered:
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.drawRoundedRect(self.rect(), 3, 3)

        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(self.rect(), Qt.AlignCenter, self.symbol)


class ToolBarBar(QGraphicsWidget):
    """Панель инструментов (Тулбар) проектируемой формы (без кнопок сетки)"""

    save_clicked = Signal()
    cut_clicked = Signal()
    copy_clicked = Signal()
    paste_clicked = Signal()
    align_left_clicked = Signal()
    align_center_clicked = Signal()
    align_right_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bar_height = 32
        self.setZValue(99)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGraphicsLinearLayout(Qt.Horizontal)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Кнопка Сохранить
        self.btn_save = ToolBarButton("💾", "Сохранить форму", self)
        self.btn_save.clicked.connect(lambda: self.save_clicked.emit())
        layout.addItem(self.btn_save)

        layout.addStretch(0.1)

        # Кнопки Вырезать/Копировать/Вставить
        self.btn_cut = ToolBarButton("✂️", "Вырезать", self)
        self.btn_cut.clicked.connect(lambda: self.cut_clicked.emit())
        layout.addItem(self.btn_cut)

        self.btn_copy = ToolBarButton("📋", "Копировать", self)
        self.btn_copy.clicked.connect(lambda: self.copy_clicked.emit())
        layout.addItem(self.btn_copy)

        self.btn_paste = ToolBarButton("📌", "Вставить", self)
        self.btn_paste.clicked.connect(lambda: self.paste_clicked.emit())
        layout.addItem(self.btn_paste)

        layout.addStretch(0.1)

        # Кнопки выравнивания
        self.btn_align_left = ToolBarButton("⬅️", "Выровнять по левому краю", self)
        self.btn_align_left.clicked.connect(lambda: self.align_left_clicked.emit())
        layout.addItem(self.btn_align_left)

        self.btn_align_center = ToolBarButton("⬌", "Выровнять по центру", self)
        self.btn_align_center.clicked.connect(lambda: self.align_center_clicked.emit())
        layout.addItem(self.btn_align_center)

        self.btn_align_right = ToolBarButton("➡️", "Выровнять по правому краю", self)
        self.btn_align_right.clicked.connect(lambda: self.align_right_clicked.emit())
        layout.addItem(self.btn_align_right)

        layout.addStretch()

        self.setLayout(layout)
        self.setMinimumHeight(self.bar_height)
        self.setMaximumHeight(self.bar_height)
        self.setMinimumWidth(500)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(self.rect())

        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())